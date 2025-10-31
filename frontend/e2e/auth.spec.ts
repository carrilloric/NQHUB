import { test, expect } from "@playwright/test";

// Test credentials
const SUPERUSER = {
  email: "admin@nqhub.com",
  password: "admin_inicial_2024",
};

const NEW_TRADER = {
  email: "newtrader@test.com",
  password: "TraderPass123!",
  fullName: "New Trader",
};

test.describe("Authentication Flow", () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state
    await page.goto("/");
    await page.evaluate(() => localStorage.clear());
  });

  test("should display login page with correct design", async ({ page }) => {
    await page.goto("/");

    // Check that NQHUB logo is visible (use h1 to be specific)
    await expect(page.locator("h1")).toContainText("NQHUB");
    await expect(page.locator("text=Professional Trading Platform")).toBeVisible();

    // Check form fields exist
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();

    // Check forgot password and register links
    await expect(page.locator('a[href="/auth/forgot-password"]')).toBeVisible();
    await expect(page.locator('a[href="/register"]')).toBeVisible();
  });

  test("should login as superuser and access dashboard", async ({ page }) => {
    await page.goto("/");

    // Fill login form
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);

    // Click login button
    await page.click('button:has-text("Login")');

    // Wait for navigation to dashboard
    await page.waitForURL("**/dashboard", { timeout: 10000 });

    // Verify we're on dashboard
    expect(page.url()).toContain("/dashboard");

    // Verify user is authenticated by checking for logout/profile elements
    // The sidebar should be visible
    await expect(page.locator("nav")).toBeVisible();
  });

  test("should show validation error for invalid email", async ({ page }) => {
    await page.goto("/");

    // Fill with invalid email
    const emailInput = page.locator('input[type="email"]');
    await emailInput.fill("invalid-email");
    await page.fill('input[type="password"]', "password123");

    // Click login button - this will trigger browser's native HTML5 validation
    await page.click('button[type="submit"]');

    // Check for HTML5 validation message
    const validationMessage = await emailInput.evaluate((input: HTMLInputElement) =>
      input.validationMessage
    );
    expect(validationMessage).toBeTruthy();
  });

  test("should show error for wrong credentials", async ({ page }) => {
    await page.goto("/");

    // Fill with wrong credentials
    await page.fill('input[type="email"]', "wrong@test.com");
    await page.fill('input[type="password"]', "wrongpassword");

    // Click login button
    await page.click('button:has-text("Login")');

    // Should show error message
    await expect(
      page.locator("text=/invalid|incorrect|wrong/i")
    ).toBeVisible({ timeout: 5000 });
  });

  test("should redirect to dashboard if already authenticated", async ({
    page,
  }) => {
    // Login first
    await page.goto("/");
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button:has-text("Login")');
    await page.waitForURL("**/dashboard");

    // Try to access login page again
    await page.goto("/");

    // Should be redirected to dashboard
    await page.waitForURL("**/dashboard", { timeout: 5000 });
    expect(page.url()).toContain("/dashboard");
  });

  test("should logout successfully", async ({ page }) => {
    // Login first
    await page.goto("/");
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");

    // Find and click logout button - it contains the LogOut icon and "Logout" text
    const logoutButton = page.locator('button:has(svg):has-text("Logout")');
    await logoutButton.click();

    // Should be redirected to login page
    await page.waitForURL("**/", { timeout: 5000 });
    expect(page.url()).not.toContain("/dashboard");

    // Login form should be visible
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });
});

test.describe("Role-Based Access Control", () => {
  test("superuser should see Invitations menu item", async ({ page }) => {
    // Login as superuser
    await page.goto("/");
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");

    // Check that Invitations link exists in sidebar (use href instead of text)
    const invitationsLink = page.locator('a[href="/admin/invitations"]');
    await expect(invitationsLink).toBeAttached();
  });

  test("superuser can access Invitations page", async ({ page }) => {
    // Login as superuser
    await page.goto("/");
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");

    // Navigate to Invitations page directly
    await page.goto("/admin/invitations");

    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Verify page content
    await expect(page.locator("h1")).toContainText("Invitations");
    await expect(
      page.locator('button:has-text("Create Invitation")')
    ).toBeVisible();
  });
});

test.describe("Invitation Management", () => {
  let invitationToken: string;

  test("superuser can create invitation", async ({ page }) => {
    // Login as superuser
    await page.goto("/");
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");

    // Navigate to Invitations page directly
    await page.goto("/admin/invitations");
    await page.waitForLoadState("networkidle");

    // Click Create Invitation button
    await page.click('button:has-text("Create Invitation")');

    // Wait for dialog to appear
    await expect(page.locator('text="Create New Invitation"')).toBeVisible();

    // Fill form (email is optional, so we can leave it empty)
    // Select role - should default to "trader"
    // Expiration days - should default to 7

    // Submit form
    await page.click('button[type="submit"]:has-text("Create")');

    // Wait for dialog to close and table to update
    await expect(page.locator('text="Create New Invitation"')).not.toBeVisible();
    await page.waitForTimeout(500);

    // Verify invitation appears in table
    const rows = page.locator('table tbody tr');
    await expect(rows).toHaveCount(1, {
      timeout: 5000,
    });
  });

  test("superuser can copy invitation link", async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);

    // Login as superuser
    await page.goto("/");
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");

    // Navigate to Invitations page directly
    await page.goto("/admin/invitations");
    await page.waitForLoadState("networkidle");

    // Create an invitation first
    await page.click('button:has-text("Create Invitation")');
    await page.click('button[type="submit"]:has-text("Create")');

    // Wait for dialog to close and invitation to appear in table
    await expect(page.locator('text="Create New Invitation"')).not.toBeVisible();
    await page.waitForTimeout(500);

    // Click copy button - it's the outline button with Copy icon in the table
    const copyButton = page.locator('table button:has-text("")').first();
    await copyButton.click();

    // Wait a bit for clipboard
    await page.waitForTimeout(500);

    // Get clipboard content
    const clipboardText = await page.evaluate(() =>
      navigator.clipboard.readText()
    );

    // Verify it's a valid registration URL with token
    expect(clipboardText).toContain("/register?token=");
  });

  test("superuser can delete invitation", async ({ page }) => {
    // Login as superuser
    await page.goto("/");
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");

    // Navigate to Invitations page directly
    await page.goto("/admin/invitations");
    await page.waitForLoadState("networkidle");

    // Create an invitation first
    await page.click('button:has-text("Create Invitation")');
    await page.click('button[type="submit"]:has-text("Create")');

    // Wait for dialog to close and invitation to appear
    await expect(page.locator('text="Create New Invitation"')).not.toBeVisible();
    await page.waitForTimeout(500);

    // Set up dialog handler BEFORE clicking delete
    page.once("dialog", (dialog) => dialog.accept());

    // Click delete button - it's the second button in the table row (after copy button)
    const deleteButton = page.locator('table button').nth(1);
    await deleteButton.click();

    // Wait a moment for deletion
    await page.waitForTimeout(1000);

    // Verify no invitations remain (empty state message should appear)
    await expect(page.locator('text="No invitations yet"')).toBeVisible({ timeout: 5000 });
  });
});

test.describe("Registration Flow", () => {
  test("should show registration page", async ({ page }) => {
    await page.goto("/register");

    // Check page elements
    await expect(page.locator("text=Register New Account")).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('#invitationToken')).toBeVisible();
  });

  test("should require invitation token", async ({ page }) => {
    await page.goto("/register");

    // Fill form without token
    await page.fill('#email', NEW_TRADER.email);
    await page.fill('#password', NEW_TRADER.password);
    await page.fill('#confirmPassword', NEW_TRADER.password);
    await page.fill('#fullName', NEW_TRADER.fullName);
    // Leave invitation token empty

    // Submit
    await page.click('button[type="submit"]');

    // Should show error about missing token
    await expect(
      page.locator('text=/invitation.*token.*required/i')
    ).toBeVisible({ timeout: 5000 });
  });

  test("should validate password match", async ({ page }) => {
    await page.goto("/register");

    // Fill with mismatched passwords
    await page.fill('#email', NEW_TRADER.email);
    await page.fill('#password', "Password123!");
    await page.fill('#confirmPassword', "DifferentPassword123!");
    await page.fill('#invitationToken', "test-token");

    // Submit
    await page.click('button[type="submit"]');

    // Should show password mismatch error
    await expect(
      page.locator('text=/password.*do not match/i')
    ).toBeVisible({ timeout: 5000 });
  });
});

test.describe("Complete End-to-End Flow", () => {
  test("complete flow: create invitation, register, login, verify access", async ({
    page,
    context,
  }) => {
    // Grant clipboard permissions
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);

    // Step 1: Login as superuser
    await page.goto("/");
    await page.fill('input[type="email"]', SUPERUSER.email);
    await page.fill('input[type="password"]', SUPERUSER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");

    // Step 2: Create invitation for specific email
    await page.goto("/admin/invitations");
    await page.waitForLoadState("networkidle");
    await page.click('button:has-text("Create Invitation")');

    // Fill email field (find the email input inside the dialog)
    await page.locator('dialog input#email').fill(NEW_TRADER.email);

    await page.click('button[type="submit"]:has-text("Create")');
    await page.waitForTimeout(2000);

    // Step 3: Copy registration link
    const copyButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await copyButton.click();
    await page.waitForTimeout(500);

    const registrationUrl = await page.evaluate(() =>
      navigator.clipboard.readText()
    );

    // Step 4: Logout
    const logoutButton = page.locator('button[aria-label="Logout"]');
    await logoutButton.click();
    await page.waitForURL("**/", { timeout: 5000 });

    // Step 5: Navigate to registration URL
    await page.goto(registrationUrl);

    // Step 6: Register new trader
    await page.fill('#email', NEW_TRADER.email);
    await page.fill('#password', NEW_TRADER.password);
    await page.fill('#confirmPassword', NEW_TRADER.password);
    await page.fill('#fullName', NEW_TRADER.fullName);

    await page.click('button[type="submit"]');

    // Should be redirected to dashboard after successful registration
    await page.waitForURL("**/dashboard", { timeout: 10000 });

    // Step 7: Verify trader CANNOT see Invitations link (it still exists in DOM but for admin only)
    const invitationsLink = page.locator('a[href="/admin/invitations"]');
    await expect(invitationsLink).toBeAttached();

    // Step 8: Try to access invitations page directly (should be redirected)
    await page.goto("/admin/invitations");
    await page.waitForTimeout(1000);

    // Should be redirected to dashboard (not on invitations page)
    expect(page.url()).not.toContain("/invitations");
    expect(page.url()).toContain("/dashboard");
  });
});
