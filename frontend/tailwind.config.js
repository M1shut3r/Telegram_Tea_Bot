export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: '#0b0c10',
          deep: '#181a21',
        },
        cream: '#d7dbe3',
        ink: '#e6e8ee',
        forest: {
          DEFAULT: '#1c1f27',
          deep: '#07080b',
        },
        gold: {
          DEFAULT: '#7dcec0',
          soft: '#9ee0d4',
        },
        neon: '#67e8c8',
        night: '#0b0c10',
        panel: '#15171d',
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
        sans: ['Outfit', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Outfit', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        neon: ['"Russo One"', 'Outfit', 'sans-serif'],
      },
      boxShadow: {
        card: '0 18px 40px rgba(0, 0, 0, 0.28)',
      },
      letterSpacing: {
        maison: '0.28em',
      },
    },
  },
  plugins: [],
}
