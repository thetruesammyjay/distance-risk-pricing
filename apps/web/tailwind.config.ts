import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        ink: '#102a43',
        teal: '#087f8c',
        mist: '#f2f7f8',
        amber: '#d97706',
      },
      boxShadow: {
        soft: '0 18px 50px rgba(16, 42, 67, 0.08)',
      },
    },
  },
  plugins: [],
};

export default config;

