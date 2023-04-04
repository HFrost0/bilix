import {defineConfig} from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "bilix",
  description: "bilix download",
  base: '/bilix/',
  lastUpdated: true,
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    editLink: {
      pattern: 'https://github.com/HFrost0/bilix/edit/master/docs/:path'
    },
    algolia: {
      appId: 'F4ZDY9KUXU',
      apiKey: '30aaace8ddea0d6f25ac39ea70ce8bd8',
      indexName: 'bilix'
    },
    footer: {
      message: 'Released under the Apache 2.0 License.',
      copyright: 'Copyright © 2022-present HFrost0'
    },
    socialLinks: [
      {icon: 'github', link: 'https://github.com/HFrost0/bilix'}
    ]
  },

  locales: {
    root: {
      label: '中文',
      lang: 'zh',
      themeConfig: {
        nav: [
          {text: 'Home', link: '/'},
          {text: '安装', link: '/install'},
          {text: '快速上手', link: '/quickstart'}
        ],
        sidebar: [
          {text: '安装', link: '/install'},
          {text: '快速上手', link: '/quickstart'},
          {text: '进阶使用', link: '/advance_guide'},
          {
            text: 'Python调用',
            items: [
              {text: '异步基础', link: '/async'},
              {text: '下载案例', link: '/download_examples'},
              {text: 'API案例', link: '/api_examples'}
            ]
          },
          {text: '更多', link: '/more'},
        ],
      }
    },

    en: {
      label: 'English',
      lang: 'en', // optional, will be added  as `lang` attribute on `html` tag
      themeConfig: {
        nav: [
          {text: 'Home', link: '/en/'},
          {text: 'Install', link: '/en/install'},
          {text: 'Quickstart', link: '/en/quickstart'}
        ],
        sidebar: [
          {text: 'Install', link: '/en/install'},
          {text: 'Quickstart', link: '/en/quickstart'},
          {text: 'Advance Guide', link: '/en/advance_guide'},
          {
            text: 'Python API',
            items: [
              {text: 'Async basic', link: '/en/async'},
              {text: 'Download Examples', link: '/en/download_examples'},
              {text: 'API Examples', link: '/en/api_examples'}
            ]
          },
          {text: 'More', link: '/en/more'},
        ],
      },
    }
  },
})
