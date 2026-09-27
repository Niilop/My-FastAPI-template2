import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const user = {
  id: 1,
  username: 'tester',
  email: 'tester@example.com',
  created_at: '2026-01-01T12:00:00Z',
  settings: {},
}
const item = {
  id: 1,
  owner_id: 1,
  title: 'First idea',
  description: 'Some details',
  created_at: '2026-01-01T12:00:00Z',
  updated_at: '2026-01-01T12:00:00Z',
}

async function mockApi(page: Page) {
  let items: (typeof item)[] = []
  await page.route(
    (url) => url.pathname.startsWith('/api/'),
    async (route) => {
      const url = new URL(route.request().url())
      const path = url.pathname
      const method = route.request().method()
      if (path === '/api/auth/login') {
        expect(route.request().postData()).toContain('username=tester')
        await route.fulfill({ json: { access_token: 'test-token', token_type: 'bearer' } })
      } else if (path === '/api/auth/register') {
        expect(route.request().postDataJSON()).toMatchObject({
          email: user.email,
          username: user.username,
        })
        await route.fulfill({ status: 201, json: user })
      } else if (path === '/api/example/') {
        expect(route.request().postDataJSON()).toEqual({
          name: 'Developer',
          task: 'Test the connection',
        })
        await route.fulfill({ json: { result: 'Request received.' } })
      } else {
        expect(route.request().headers().authorization).toBe('Bearer test-token')
        if (path === '/api/auth/me') await route.fulfill({ json: user })
        else if (path === '/api/items' && method === 'GET') {
          const offset = Number(url.searchParams.get('offset'))
          const limit = Number(url.searchParams.get('limit'))
          await route.fulfill({
            json: { items: items.slice(offset, offset + limit), total: items.length },
          })
        } else if (path === '/api/items' && method === 'POST') {
          const body = route.request().postDataJSON()
          expect(Object.keys(body).sort()).toEqual(['description', 'title'])
          const created = { ...item, ...body, id: items.length + 1 }
          items.unshift(created)
          await route.fulfill({ status: 201, json: created })
        } else if (path === '/api/items/1' && method === 'PUT') {
          items[0] = { ...items[0], ...route.request().postDataJSON() }
          await route.fulfill({ json: items[0] })
        } else if (path === '/api/items/1' && method === 'DELETE') {
          items = []
          await route.fulfill({ status: 204 })
        } else await route.fulfill({ status: 404, json: { detail: 'Not found' } })
      }
    },
  )
}

async function signIn(page: Page) {
  await page.getByLabel('Email or username').fill('tester')
  await page.getByLabel('Password', { exact: true }).fill('a-long-test-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
}

test.beforeEach(async ({ page }) => {
  await mockApi(page)
})

test('public example and unknown routes', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Send request' }).click()
  await expect(page.getByRole('status')).toHaveText('Request received.')
  await page.goto('/missing')
  await expect(page.getByRole('heading', { name: 'Page not found' })).toBeVisible()
})

test('protected route, item lifecycle, account and sign out', async ({ page }) => {
  await page.goto('/items')
  await expect(page).toHaveURL(/\/login$/)
  await signIn(page)
  await expect(page).toHaveURL(/\/items$/)
  await expect(page.getByRole('heading', { name: 'No items here' })).toBeVisible()
  await page.getByLabel('Title', { exact: true }).fill('First idea')
  await page.getByLabel('Description').fill('Some details')
  await page.getByRole('button', { name: 'Create item' }).click()
  await expect(page.getByRole('status')).toHaveText('Item created.')
  await expect(
    page.getByRole('cell', { name: 'First idea Some details', exact: true }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Edit First idea', exact: true }).click()
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue('First idea')
  await page.getByLabel('Title', { exact: true }).fill('Updated idea')
  await page.getByRole('button', { name: 'Save changes' }).click()
  await expect(page.getByRole('status')).toHaveText('Item updated.')
  await page.getByRole('button', { name: 'Edit Updated idea', exact: true }).click()
  await page.getByRole('button', { name: 'Cancel edit' }).click()
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue('')
  await page.getByRole('button', { name: 'Delete Updated idea', exact: true }).click()
  await page.getByRole('button', { name: 'Cancel delete' }).click()
  await expect(
    page.getByRole('cell', { name: 'Updated idea Some details', exact: true }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Delete Updated idea', exact: true }).click()
  await page.getByRole('button', { name: 'Confirm delete' }).click()
  await expect(page.getByRole('status')).toHaveText('Item deleted.')
  await expect(page.getByRole('heading', { name: 'No items here' })).toBeVisible()
  await page.getByRole('link', { name: 'Account', exact: true }).click()
  await expect(page.getByText('tester@example.com', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page).toHaveURL(/\/login$/)
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([])
  expect(await page.evaluate(() => Object.keys(sessionStorage))).toEqual([])
})

test('registration and server validation errors', async ({ page }) => {
  await page.goto('/register')
  await page.getByLabel('Email', { exact: true }).fill(user.email)
  await page.getByLabel('Username', { exact: true }).fill(user.username)
  await page.getByLabel('Password', { exact: true }).fill('a-long-test-password')
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('status')).toHaveText('Account created. You can now sign in.')
  await page.route('**/api/auth/login', (route) =>
    route.fulfill({
      status: 422,
      json: { detail: [{ loc: ['body', 'username'], msg: 'Invalid username' }] },
    }),
  )
  await signIn(page)
  await expect(page.getByRole('alert')).toHaveText('Invalid username')
})

test('expired credentials clear the session', async ({ page }) => {
  await page.goto('/login')
  await signIn(page)
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
  await page.route('**/api/items?*', (route) =>
    route.fulfill({
      status: 401,
      json: { detail: 'Invalid or expired token' },
    }),
  )
  await page.getByRole('link', { name: 'Items', exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('button', { name: 'Sign out' })).toHaveCount(0)
})

test('network failures display an error and allow retry', async ({ page }) => {
  await page.goto('/')
  await page.route('**/api/example/', (route) => route.abort())
  await page.getByRole('button', { name: 'Send request' }).click()
  await expect(page.getByRole('alert')).toHaveText('Cannot reach the server. Please try again.')
  await expect(page.getByRole('button', { name: 'Send request' })).toBeEnabled()
})

test('failed item saves keep the draft for retry', async ({ page }) => {
  await page.goto('/items')
  await signIn(page)
  await expect(page.getByRole('heading', { name: 'Add an item' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Create item' })).toBeDisabled()
  await page.getByLabel('Title', { exact: true }).fill('Keep my draft')
  await page.getByLabel('Description').fill('Do not lose this')
  let fail = true
  await page.route('**/api/items', (route) => {
    if (!fail) return route.fallback()
    fail = false
    return route.fulfill({ status: 503, json: { detail: 'Please try again' } })
  })
  await page.getByRole('button', { name: 'Create item' }).click()
  await expect(page.getByRole('alert')).toHaveText('Please try again')
  await expect(page.getByLabel('Title', { exact: true })).toHaveValue('Keep my draft')
  await expect(page.getByLabel('Description')).toHaveValue('Do not lose this')
  await page.getByRole('button', { name: 'Create item' }).click()
  await expect(
    page.getByRole('cell', { name: 'Keep my draft Do not lose this', exact: true }),
  ).toBeVisible()
})

test('pagination returns to the previous page after deleting its last item', async ({ page }) => {
  let items = Array.from({ length: 21 }, (_, index) => ({
    ...item,
    id: index + 1,
    title: `Item ${index + 1}`,
  }))
  await page.route('**/api/items?*', (route) => {
    const offset = Number(new URL(route.request().url()).searchParams.get('offset'))
    return route.fulfill({ json: { items: items.slice(offset, offset + 20), total: items.length } })
  })
  await page.route('**/api/items/21', (route) => {
    expect(route.request().method()).toBe('DELETE')
    items = items.filter((entry) => entry.id !== 21)
    return route.fulfill({ status: 204 })
  })
  await page.goto('/items')
  await signIn(page)
  await expect(page.getByText('21 items · Page 1')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Previous' })).toBeDisabled()
  await page.getByRole('button', { name: 'Next', exact: true }).click()
  await expect(page.getByText('21 items · Page 2')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: 'Delete Item 21', exact: true }).click()
  await page.getByRole('button', { name: 'Confirm delete' }).click()
  await expect(page.getByText('20 items · Page 1')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Previous' })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeDisabled()
})
