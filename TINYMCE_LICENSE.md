# TinyMCE License Configuration

TinyMCE 6+ requires a license key, even for free self-hosted deployments.

## Current Configuration

The project is configured to use the **GPL self-hosted license** which is free:

```javascript
license_key: 'gpl'
```

This is set in `webengine/assets/js/tinymce-init.js`.

## License Options

### Option 1: GPL Self-Hosted (Free) ✅ CURRENT
- **License Key:** `'gpl'`
- **Cost:** Free
- **Usage:** Self-hosted, GPL-compliant projects
- **Limitations:** Must comply with GPL v2+ license
- **Setup:** Already configured!

### Option 2: TinyMCE Cloud (Free Tier)
- **License Key:** Get from https://www.tiny.cloud/auth/signup/
- **Cost:** Free up to 1,000 editor loads/month
- **Usage:** Any project type
- **Benefits:** 
  - CDN-hosted plugins
  - Premium features in free tier
  - No GPL requirements
- **Setup:** 
  1. Sign up at https://www.tiny.cloud/auth/signup/
  2. Get your API key from the dashboard
  3. Replace `'gpl'` with your key in `tinymce-init.js`

### Option 3: TinyMCE Premium
- **Cost:** Paid plans from $49/month
- **Benefits:** Advanced features, priority support
- **Not needed for basic usage**

## What's Included in GPL Version

The GPL version includes:
- ✅ Core rich text editing
- ✅ Basic formatting (bold, italic, underline)
- ✅ Lists (bullets, numbers)
- ✅ Links and images
- ✅ Tables
- ✅ Code view
- ✅ Word count
- ✅ Full toolbar customization

## Troubleshooting

If you see license warnings:
1. Verify `license_key: 'gpl'` is set in `tinymce-init.js`
2. Clear browser cache and reload
3. Check browser console for errors

If you need premium features:
1. Sign up for free cloud tier
2. Or purchase a premium license
3. Update the `license_key` in the config

## More Information

- GPL License: https://www.gnu.org/licenses/gpl-2.0.html
- TinyMCE Pricing: https://www.tiny.cloud/pricing/
- Self-Hosting Guide: https://www.tiny.cloud/docs/tinymce/latest/self-hosting/
