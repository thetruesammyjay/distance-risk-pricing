import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        violet: '#5423e7',
        iris: '#7047eb',
        lemon: '#ffc233',
        orchid: '#cf75ff',
        lilac: '#e5b5fe',
        crimson: '#d50b3e',
        ink: '#121217',
        paper: '#ffffff',
        fog: '#f7f7f8',
        slate: '#6c6c89',
        ash: '#d1d1db',
      },
      boxShadow: {
        soft: '0 4px 24px rgba(18, 18, 23, 0.06)',
        console: '0 20px 60px rgba(18, 18, 23, 0.18)',
      },
      borderRadius: {
        control: '8px',
      },
    },
  },
  plugins: [],
};

export default config;
