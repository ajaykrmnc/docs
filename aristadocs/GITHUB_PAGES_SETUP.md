# GitHub Pages Setup Guide

This repository is configured to automatically deploy documentation to GitHub Pages using VitePress and GitHub Actions.

## 📋 Overview

The documentation site is built using:
- **VitePress** - Modern static site generator powered by Vue
- **Node.js 20 LTS** - Runtime environment
- **GitHub Actions** - Automated deployment pipeline

## 🚀 Quick Start

### Enable GitHub Pages

1. **Go to your GitHub repository settings:**
   - Navigate to `https://github.com/ajaykrmnc/docs/settings/pages`

2. **Configure GitHub Pages:**
   - Under "Build and deployment"
   - Source: Select **GitHub Actions**
   - (No need to select a branch when using GitHub Actions)

3. **Push your changes:**
   ```bash
   git add .
   git commit -m "Add GitHub Pages configuration with VitePress"
   git push origin master
   ```

4. **Monitor the deployment:**
   - Go to the "Actions" tab in your repository
   - Watch the "Deploy VitePress site to GitHub Pages" workflow
   - Once complete, your site will be live!

### Access Your Site

After deployment, your site will be available at:
```
https://ajaykrmnc.github.io/docs/
```

## 💻 Local Development

1. **Navigate to the aristadocs directory:**
   ```bash
   cd aristadocs
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run docs:dev
   ```
   The site will be available at `http://localhost:5173`

4. **Build for production:**
   ```bash
   npm run docs:build
   ```
   The built site will be in the `.vitepress/dist/` directory

5. **Preview production build:**
   ```bash
   npm run docs:preview
   ```

## 📁 Project Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions workflow
├── aristadocs/
│   ├── .vitepress/
│   │   ├── config.mjs              # VitePress configuration
│   │   └── dist/                   # Generated site (git-ignored)
│   ├── index.md                    # Homepage
│   ├── package.json                # Node.js dependencies
│   ├── build-and-tooling/          # Documentation sections
│   ├── kernel-and-system/
│   ├── networking/
│   ├── wifi-and-wireless/
│   └── wlan-drivers/
└── README.md
```

## 🔧 Configuration Files

### `.github/workflows/deploy.yml`
The GitHub Actions workflow that:
- Triggers on pushes to the `master` branch
- Uses Node.js 20 LTS
- Installs dependencies with `npm ci`
- Builds the site with `npm run docs:build`
- Deploys to GitHub Pages using official GitHub Actions
- Can be manually triggered from the Actions tab

### `aristadocs/.vitepress/config.mjs`
VitePress configuration including:
- Site title and description
- Base path: `/docs/` (for GitHub Pages URL structure)
- Navigation menu
- Sidebar structure
- Search functionality
- Theme customization
- GitHub social link

### `aristadocs/package.json`
Defines:
- VitePress dependency
- Build scripts
- Project metadata

## 🌐 GitHub Pages Deployment

### Automatic Deployment

When you push to the `master` branch:
1. GitHub Actions automatically triggers the deployment workflow
2. Dependencies are installed
3. The site is built from the `aristadocs` directory
4. The `.vitepress/dist` directory is deployed to GitHub Pages
5. Your site is updated within minutes

### Manual Deployment

You can also trigger a manual deployment:
1. Go to your GitHub repository
2. Navigate to **Actions** tab
3. Select "Deploy VitePress site to GitHub Pages"
4. Click **Run workflow**
5. Select the `master` branch
6. Click **Run workflow**

### Deployment Status

Check deployment status:
- **Actions tab**: See workflow runs and logs
- **Settings > Pages**: See deployment history and current status
- **Environments**: See deployment environments and URLs

## 📝 Adding Documentation

1. Create or edit Markdown files in the appropriate directory under `aristadocs/`
2. Update `aristadocs/.vitepress/config.mjs` to add the page to navigation/sidebar
3. Commit and push to trigger automatic deployment

### Markdown Tips

- Use standard Markdown syntax
- Code blocks support syntax highlighting
- Frontmatter (YAML) is supported for page metadata
- Avoid using `{{ }}` or `<tag>` patterns outside code blocks (they're escaped automatically)

## 🐛 Troubleshooting

### Build Fails Locally

```bash
# Clear cache and rebuild
cd aristadocs
rm -rf node_modules .vitepress/cache .vitepress/dist
npm install
npm run docs:build
```

### Workflow Fails on GitHub

1. Check the workflow logs in the Actions tab
2. Ensure `.github/workflows/deploy.yml` is in the repository root
3. Verify `aristadocs/package.json` and `aristadocs/.vitepress/config.mjs` are present
4. Check for syntax errors in Markdown files
5. Ensure GitHub Pages is enabled in repository settings

### Site Not Loading or 404 Errors

1. Verify the base path in `config.mjs` matches your repository name: `base: '/docs/'`
2. Check that GitHub Pages source is set to "GitHub Actions"
3. Wait a few minutes after deployment completes
4. Clear your browser cache

### Dead Links Warning

The configuration currently ignores dead links (`ignoreDeadLinks: true`). To fix dead links:
1. Set `ignoreDeadLinks: false` in `aristadocs/.vitepress/config.mjs`
2. Run `npm run docs:build` to see all dead links
3. Fix or remove the broken links

## 🔄 Updating VitePress

```bash
cd aristadocs
npm update vitepress
```

## 📚 Resources

- [VitePress Documentation](https://vitepress.dev/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Markdown Guide](https://www.markdownguide.org/)

## ✅ Setup Checklist

- [x] `.github/workflows/deploy.yml` created
- [x] `aristadocs/package.json` with VitePress dependency
- [x] `aristadocs/.vitepress/config.mjs` configured with correct base path
- [x] `aristadocs/index.md` homepage
- [x] GitHub Actions workflow tested
- [ ] GitHub Pages enabled in repository settings (you need to do this)
- [ ] First deployment successful
- [ ] Site accessible at https://ajaykrmnc.github.io/docs/

## 🎯 Next Steps

1. **Enable GitHub Pages in repository settings:**
   - Go to https://github.com/ajaykrmnc/docs/settings/pages
   - Set Source to "GitHub Actions"

2. **Push these changes to GitHub:**
   ```bash
   git add .
   git commit -m "Add GitHub Pages configuration with VitePress"
   git push origin master
   ```

3. **Monitor the deployment:**
   - Go to https://github.com/ajaykrmnc/docs/actions
   - Watch the workflow run

4. **Access your site:**
   - Once deployed, visit https://ajaykrmnc.github.io/docs/

5. **Customize:**
   - Update navigation and sidebar in `aristadocs/.vitepress/config.mjs`
   - Add more documentation pages
   - Customize the theme

## 🔐 Permissions

The workflow requires the following permissions (already configured in `deploy.yml`):
- `contents: read` - To checkout the repository
- `pages: write` - To deploy to GitHub Pages
- `id-token: write` - For GitHub Pages deployment authentication

These are automatically granted when you enable GitHub Pages with GitHub Actions.

## 🆚 GitHub Pages vs GitLab Pages

This repository supports both:
- **GitHub Pages**: Uses `.github/workflows/deploy.yml` and GitHub Actions
- **GitLab Pages**: Uses `.gitlab-ci.yml` (if you mirror to GitLab)

Both configurations are independent and can coexist. The VitePress base path is set for GitHub Pages (`/docs/`). If you also use GitLab Pages, you may need to adjust the base path accordingly or use environment variables.


