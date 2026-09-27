import { randomUUID } from 'node:crypto'
import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import type { Item, Token } from '../src/api/types'

const password = 'smoke-test-password-123'

async function register(page: Page, username: string) {
  await page.goto('/register')
  await page.getByLabel('Email', { exact: true }).fill(`${username}@example.com`)
  await page.getByLabel('Username', { exact: true }).fill(username)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Create account', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
}

async function signIn(page: Page, username: string) {
  await page.getByLabel('Email or username').fill(username)
  await page.getByLabel('Password', { exact: true }).fill(password)
  const login = page.waitForResponse(
    (response) => new URL(response.url()).pathname === '/api/auth/login',
  )
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  const response = await login
  expect(response.status()).toBe(200)
  const token: Token = await response.json()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
  return { Authorization: `Bearer ${token.access_token}` }
}

test('real registration, login, persistence, ownership and item CRUD', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  const username = `smoke-${randomUUID()}`
  const ready = await page.request.get('/api/ready')
  expect(ready.status()).toBe(200)
  await register(page, username)
  const ownerHeaders = await signIn(page, username)
  await page.getByRole('link', { name: 'Items', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'No items here' })).toBeVisible()
  await page.getByLabel('Title', { exact: true }).fill('Private smoke item')
  await page.getByLabel('Description').fill('Stored in PostgreSQL')
  const creation = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === '/api/items' && response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Create item' }).click()
  const created = await creation
  expect(created.status()).toBe(201)
  const item: Item = await created.json()
  await expect(page.getByRole('status')).toHaveText('Item created.')

  // A new page/session must load the saved record from the real API.
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  await signIn(page, username)
  await expect(
    page.getByRole('cell', { name: 'Private smoke item Stored in PostgreSQL', exact: true }),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Edit Private smoke item', exact: true }).click()
  await page.getByLabel('Title', { exact: true }).fill('Updated smoke item')
  await page.getByRole('button', { name: 'Save changes' }).click()
  await expect(page.getByRole('status')).toHaveText('Item updated.')

  await page.getByRole('button', { name: 'Sign out' }).click()
  const otherName = `other-${randomUUID()}`
  await register(page, otherName)
  const otherHeaders = await signIn(page, otherName)
  await page.getByRole('link', { name: 'Items', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'No items here' })).toBeVisible()
  const path = `/api/items/${item.id}`
  expect((await page.request.get(path)).status()).toBe(401)
  const otherList = await page.request.get('/api/items', { headers: otherHeaders })
  expect(otherList.status()).toBe(200)
  expect(await otherList.json()).toEqual({ items: [], total: 0 })
  for (const method of ['GET', 'PUT', 'DELETE']) {
    const response = await page.request.fetch(path, {
      method,
      headers: otherHeaders,
      ...(method === 'PUT' ? { data: { title: 'Unauthorized edit' } } : {}),
    })
    expect(response.status()).toBe(404)
  }
  const stored = await page.request.get(path, { headers: ownerHeaders })
  expect(stored.status()).toBe(200)
  expect((await stored.json()).title).toBe('Updated smoke item')

  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  await signIn(page, username)
  await page.getByRole('link', { name: 'Items', exact: true }).click()
  await page.getByRole('button', { name: 'Delete Updated smoke item', exact: true }).click()
  await page.getByRole('button', { name: 'Confirm delete' }).click()
  await expect(page.getByRole('heading', { name: 'No items here' })).toBeVisible()
  expect((await page.request.get(path, { headers: ownerHeaders })).status()).toBe(404)
  expect(errors).toEqual([])
})
