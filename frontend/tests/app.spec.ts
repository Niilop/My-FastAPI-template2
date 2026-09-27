import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const user = {
  id: 1,
  username: 'tester',
  email: 'tester@example.com',
  created_at: '2026-01-01T12:00:00Z',
  settings: {},
}
const dataset = {
  id: 1,
  name: 'Sales',
  description: 'Monthly totals',
  created_at: '2026-01-01T12:00:00Z',
  updated_at: '2026-01-01T12:00:00Z',
  data_metadata: {
    num_rows: 2,
    num_cols: 2,
    columns: ['month', 'total'],
    missing_values: { month: 0, total: 0 },
  },
}

async function mockApi(page: Page) {
  let uploaded = false
  await page.route(
    (url) => url.pathname.startsWith('/api/'),
    async (route) => {
      const path = new URL(route.request().url()).pathname
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
        else if (path === '/api/data/catalog')
          await route.fulfill({ json: uploaded ? [dataset] : [] })
        else if (path === '/api/data/count')
          await route.fulfill({
            json: { count: uploaded ? 1 : 0, limit: 10, remaining: uploaded ? 9 : 10 },
          })
        else if (path === '/api/data/upload') {
          expect(route.request().headers()['content-type']).toContain(
            'multipart/form-data; boundary=',
          )
          expect(route.request().postData()).toContain('month,total')
          uploaded = true
          await route.fulfill({ status: 201, json: dataset })
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

test('protected route, upload, account and sign out', async ({ page }) => {
  await page.goto('/datasets')
  await expect(page).toHaveURL(/\/login$/)
  await signIn(page)
  await expect(page).toHaveURL(/\/datasets$/)
  await expect(page.getByRole('heading', { name: 'No datasets yet' })).toBeVisible()
  await page.getByLabel('Name', { exact: true }).fill('Sales')
  await page.getByLabel('Description').fill('Monthly totals')
  await page.getByLabel('CSV file').setInputFiles({
    name: 'sales.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from('month,total\nJanuary,10\nFebruary,20\n'),
  })
  await page.getByRole('button', { name: 'Upload dataset' }).click()
  await expect(page.getByRole('status')).toHaveText('Dataset uploaded.')
  await expect(page.getByRole('cell', { name: /Sales/ })).toBeVisible()
  await expect(page.getByText('1 of 10 datasets used')).toBeVisible()
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
  await page.route('**/api/data/catalog', (route) =>
    route.fulfill({
      status: 401,
      json: { detail: 'Invalid or expired token' },
    }),
  )
  await page.getByRole('link', { name: 'Datasets', exact: true }).click()
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
