import {defineConfig} from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "bilix",
  description: "bilix download",
  base: '/bilix/',
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      {text: 'Home', link: '/'},
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

    footer: {
      message: 'Released under the Apache 2.0 License.',
      copyright: 'Copyright © 2022-present HFrost0'
    },
    socialLinks: [
      {icon: 'github', link: 'https://github.com/HFrost0/bilix'}
    ]
  },
})
