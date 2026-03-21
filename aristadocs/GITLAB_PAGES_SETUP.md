# GitLab Pages Setup Guide

This repository is configured to automatically deploy documentation to GitLab Pages using VitePress.

## 📋 Overview

The documentation site is built using:
- **VitePress** - Modern static site generator powered by Vue
- **Node.js LTS** - Runtime environment
- **GitLab CI/CD** - Automated deployment pipeline

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run docs:dev
   ```
   The site will be available at `http://localhost:5173`

3. **Build for production:**
   ```bash
   npm run build
   ```
   The built site will be in the `public/` directory

4. **Preview production build:**
   ```bash
   npm run docs:preview
   ```

## 📁 Project Structure

```
.
├── .gitlab-ci.yml              # GitLab CI/CD pipeline configuration
├── .vitepress/
│   └── config.mjs              # VitePress configuration
├── index.md                    # Homepage
├── package.json                # Node.js dependencies
├── build-and-tooling/          # Documentation sections
├── kernel-and-system/
├── networking/
├── wifi-and-wireless/
├── wlan-drivers/
└── public/                     # Generated site (git-ignored)
```

## 🔧 Configuration Files

### `.gitlab-ci.yml`
The GitLab CI/CD pipeline that:
- Uses Node.js LTS Docker image
- Installs dependencies with `npm ci`
- Builds the site with `npm run build`
- Publishes the `public/` directory to GitLab Pages
- Only runs on the default branch (main/master)

### `.vitepress/config.mjs`
VitePress configuration including:
- Site title and description
- Navigation menu
- Sidebar structure
- Search functionality
- Theme customization

### `package.json`
Defines:
- VitePress dependency
- Build scripts
- Project metadata

## 🌐 GitLab Pages Deployment

### Automatic Deployment

When you push to the default branch (main/master):
1. GitLab CI/CD automatically triggers the `pages` job
2. Dependencies are installed
3. The site is built
4. The `public/` directory is deployed to GitLab Pages

### Manual Deployment

You can also trigger a manual deployment:
1. Go to your GitLab project
2. Navigate to **CI/CD > Pipelines**
3. Click **Run Pipeline**

### Accessing Your Site

After deployment, your site will be available at:
```
https://<username>.gitlab.io/<project-name>/
```

Or your custom GitLab Pages URL if configured.

## 📝 Adding Documentation

1. Create or edit Markdown files in the appropriate directory
2. Update `.vitepress/config.mjs` to add the page to navigation/sidebar
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
rm -rf node_modules .vitepress/cache .vitepress/dist public
npm install
npm run build
```

### Pipeline Fails on GitLab

1. Check the pipeline logs in GitLab CI/CD
2. Ensure `.gitlab-ci.yml` is in the repository root
3. Verify `package.json` and `.vitepress/config.mjs` are present
4. Check for syntax errors in Markdown files

### Dead Links Warning

The configuration currently ignores dead links (`ignoreDeadLinks: true`). To fix dead links:
1. Set `ignoreDeadLinks: false` in `.vitepress/config.mjs`
2. Run `npm run build` to see all dead links
3. Fix or remove the broken links

## 🔄 Updating VitePress

```bash
npm update vitepress
```

## 📚 Resources

- [VitePress Documentation](https://vitepress.dev/)
- [GitLab Pages Documentation](https://docs.gitlab.com/ee/user/project/pages/)
- [Markdown Guide](https://www.markdownguide.org/)

## ✅ Checklist for GitLab Pages

- [x] `.gitlab-ci.yml` created
- [x] `package.json` with VitePress dependency
- [x] `.vitepress/config.mjs` configuration
- [x] `index.md` homepage
- [x] `.gitignore` for build artifacts
- [x] Markdown files escaped for Vue compatibility
- [x] Build tested locally
- [x] Ready for GitLab deployment

## 🎯 Next Steps

1. **Push to GitLab:**
   ```bash
   git add .
   git commit -m "Add GitLab Pages configuration with VitePress"
   git push origin main
   ```

2. **Monitor the pipeline** in GitLab CI/CD

3. **Access your published site** once the pipeline completes

4. **Customize** the theme and navigation in `.vitepress/config.mjs`

