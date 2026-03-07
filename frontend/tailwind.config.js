/** @type {import('tailwindcss').Config} */
module.exports = {
	darkMode: ["class"],
	content: [
		"./src/**/*.{js,jsx,ts,tsx}",
		"./public/index.html"
	],
	theme: {
		extend: {
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			colors: {
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				chart: {
					'1': 'hsl(var(--chart-1))',
					'2': 'hsl(var(--chart-2))',
					'3': 'hsl(var(--chart-3))',
					'4': 'hsl(var(--chart-4))',
					'5': 'hsl(var(--chart-5))'
				},
				/* ── Brand Design Tokens ── */
				brand: {
					black: '#09090B',      /* near-black base */
					surface: '#111116',     /* dark card surface */
					border: '#1E1E2A',      /* subtle dark border */
					violet: '#7C3AED',      /* primary brand */
					'violet-light': '#A78BFA', /* hover-glow accent */
					'violet-muted': 'rgba(124,58,237,0.12)', /* very subtle bg tint */
					emerald: '#10B981',     /* success / active */
					rose: '#F43F5E',     /* critical / alert */
					amber: '#F59E0B',     /* warning */
					white: '#FFFFFF',
					gray: '#A1A1AA',
				}
			},
			fontFamily: {
				/* Display / Headings — geometric, premium */
				heading: ['"Outfit"', 'system-ui', 'sans-serif'],
				/* Body / UI — engineered for screens */
				body: ['"Inter"', 'system-ui', 'sans-serif'],
				/* Code / Logs */
				mono: ['"JetBrains Mono"', 'monospace'],
			},
			boxShadow: {
				'glow-violet': '0 0 24px rgba(124,58,237,0.35)',
				'glow-emerald': '0 0 20px rgba(16,185,129,0.3)',
				'glow-rose': '0 0 20px rgba(244,63,94,0.3)',
				'card': '0 1px 3px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)',
				'card-hover': '0 4px 20px rgba(0,0,0,0.6), 0 0 0 1px rgba(124,58,237,0.2)',
			},
			keyframes: {
				'accordion-down': {
					from: { height: '0' },
					to: { height: 'var(--radix-accordion-content-height)' }
				},
				'accordion-up': {
					from: { height: 'var(--radix-accordion-content-height)' },
					to: { height: '0' }
				},
				'shimmer': {
					'100%': { transform: 'translateX(100%)' }
				},
				'reveal': {
					from: { opacity: '0', transform: 'translateY(18px)' },
					to: { opacity: '1', transform: 'translateY(0)' },
				},
				'reveal-scale': {
					from: { opacity: '0', transform: 'scale(0.97)' },
					to: { opacity: '1', transform: 'scale(1)' },
				},
				'float': {
					'0%, 100%': { transform: 'translateY(0px)' },
					'50%': { transform: 'translateY(-8px)' },
				},
				'glow-pulse': {
					'0%, 100%': { boxShadow: '0 0 18px rgba(124,58,237,0.3)' },
					'50%': { boxShadow: '0 0 36px rgba(124,58,237,0.6)' },
				},
				'pulse-slow': {
					'0%, 100%': { opacity: '1' },
					'50%': { opacity: '0.5' },
				},
				'slide-in-right': {
					from: { opacity: '0', transform: 'translateX(20px)' },
					to: { opacity: '1', transform: 'translateX(0)' },
				},
				'count-up': {
					from: { opacity: '0', transform: 'translateY(8px)' },
					to: { opacity: '1', transform: 'translateY(0)' },
				},
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'shimmer': 'shimmer 2s infinite',
				'reveal': 'reveal 0.7s cubic-bezier(0.16,1,0.3,1) forwards',
				'reveal-scale': 'reveal-scale 0.5s cubic-bezier(0.16,1,0.3,1) forwards',
				'float': 'float 6s ease-in-out infinite',
				'glow-pulse': 'glow-pulse 2.5s ease-in-out infinite',
				'pulse-slow': 'pulse-slow 3s ease-in-out infinite',
				'slide-in-right': 'slide-in-right 0.4s ease-out forwards',
				'count-up': 'count-up 0.4s ease-out forwards',
			}
		}
	},
	plugins: [require("tailwindcss-animate")],
};