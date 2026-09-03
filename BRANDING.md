# EventEveryday branding map

Use this checklist whenever the logo or wordmark changes so the identity stays consistent across the product.

## Logo sources

- Django admin and login shared SVG markup: `backend/templates/admin/includes/eventeveryday_logo.html`
- Public Next.js shared logo component: `frontend/components/site-logo.tsx`
- Standalone light-background asset: `backend/static/admin/img/eventeveryday-logo-light.svg`
- Standalone dark-background asset: `backend/static/admin/img/eventeveryday-logo-dark.svg`

The Django admin header and login page both consume the shared template include. All public frontend headers consume `SiteLogo`, so individual pages should not contain their own logo markup.

## Typography

- Django/Google Fonts request: `backend/templates/admin/base_site.html`
- Django logo styling and header sizing: `backend/static/admin/css/eventeveryday.css`
- Django login logo sizing: `backend/static/admin/css/eventeveryday-login.css`
- Next.js optimized logo font: `frontend/app/layout.tsx`
- Public logo sizing and colors: `frontend/app/styles.css`

## Update checklist

1. Update the shared Django SVG include and the React `SiteLogo` component.
2. Update both standalone SVG assets.
3. If the wordmark typeface changes, update both font-loading locations and the corresponding CSS font stacks.
4. Verify the admin header, admin login, homepage, event detail, and booking status views in light and dark themes.
