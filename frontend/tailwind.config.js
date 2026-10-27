export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // «Чёрный лак»: чёрный лаковый фон, золото и киноварь, как на хохломе.
        lacquer: {
          DEFAULT: '#140e0b',
          deep: '#0b0806',
          panel: '#211813',
          raised: '#2c211a',
          line: '#3a2c20',
        },
        gold: {
          DEFAULT: '#dda94a',
          bright: '#f0c46a',
          leaf: '#c39340',
          field: '#a07c3e',
          muted: '#8a6a35',
        },
        cinnabar: {
          DEFAULT: '#b8321f',
          bright: '#d6452e',
        },
        cream: {
          DEFAULT: '#f5ebdd',
          paper: '#f4ecdf',
          soft: '#bfa98c',
          dim: '#a8957a',
          muted: '#cdbba3',
        },
        sage: '#9cc28a',
        danger: '#f08a73',
        tg: {
          bg: 'var(--tg-theme-bg-color)',
          text: 'var(--tg-theme-text-color)',
          hint: 'var(--tg-theme-hint-color)',
          link: 'var(--tg-theme-link-color)',
          button: 'var(--tg-theme-button-color)',
          'button-text': 'var(--tg-theme-button-text-color)',
          secondary: 'var(--tg-theme-secondary-bg-color)',
        },
      },
      fontFamily: {
        sans: ['Nunito', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"Yeseva One"', 'Georgia', 'serif'],
      },
      letterSpacing: {
        kicker: '0.18em',
      },
    },
  },
  plugins: [],
}
