import React, { useEffect, useRef, useCallback } from 'react';

/**
 * SparklesCursor - A canvas-based particle system that creates
 * small sparkle dots that follow the mouse cursor and drift away.
 * Inspired by the Antigravity IDE website particle effect.
 */
const SparklesCursor = ({
    colors = ['#6C63FF', '#8B83FF', '#4F46E5', '#A5B4FC', '#818CF8'],
    particleCount = 2,
    fadeSpeed = 0.015,
    speedRange = { min: 0.3, max: 1.2 },
    sizeRange = { min: 1.5, max: 4 },
    spread = 25
}) => {
    const canvasRef = useRef(null);
    const particlesRef = useRef([]);
    const mouseRef = useRef({ x: -100, y: -100 });
    const animationRef = useRef(null);
    const isActiveRef = useRef(true);

    const createParticle = useCallback((x, y) => {
        const angle = Math.random() * Math.PI * 2;
        const speed = speedRange.min + Math.random() * (speedRange.max - speedRange.min);
        const size = sizeRange.min + Math.random() * (sizeRange.max - sizeRange.min);

        return {
            x: x + (Math.random() - 0.5) * spread,
            y: y + (Math.random() - 0.5) * spread,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed - 0.5, // slight upward bias
            size,
            opacity: 0.6 + Math.random() * 0.4,
            color: colors[Math.floor(Math.random() * colors.length)],
            life: 1,
            rotation: Math.random() * 360,
            rotationSpeed: (Math.random() - 0.5) * 4
        };
    }, [colors, speedRange, sizeRange, spread]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resize();
        window.addEventListener('resize', resize);

        const handleMouseMove = (e) => {
            mouseRef.current = { x: e.clientX, y: e.clientY };

            // Spawn particles on mouse move
            for (let i = 0; i < particleCount; i++) {
                particlesRef.current.push(createParticle(e.clientX, e.clientY));
            }

            // Cap the total particles for performance
            if (particlesRef.current.length > 150) {
                particlesRef.current = particlesRef.current.slice(-150);
            }
        };

        const animate = () => {
            if (!isActiveRef.current) return;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            particlesRef.current = particlesRef.current.filter(p => {
                p.x += p.vx;
                p.y += p.vy;
                p.life -= fadeSpeed;
                p.rotation += p.rotationSpeed;
                p.vx *= 0.99; // friction
                p.vy *= 0.99;

                if (p.life <= 0) return false;

                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate((p.rotation * Math.PI) / 180);
                ctx.globalAlpha = p.opacity * p.life;
                ctx.fillStyle = p.color;

                // Draw a small dot/diamond shape
                ctx.beginPath();
                const s = p.size * p.life;
                ctx.moveTo(0, -s);
                ctx.lineTo(s * 0.6, 0);
                ctx.lineTo(0, s);
                ctx.lineTo(-s * 0.6, 0);
                ctx.closePath();
                ctx.fill();

                ctx.restore();
                return true;
            });

            animationRef.current = requestAnimationFrame(animate);
        };

        window.addEventListener('mousemove', handleMouseMove);
        animationRef.current = requestAnimationFrame(animate);

        return () => {
            isActiveRef.current = false;
            window.removeEventListener('resize', resize);
            window.removeEventListener('mousemove', handleMouseMove);
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [createParticle, fadeSpeed, particleCount]);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-[60]"
            style={{ mixBlendMode: 'screen' }}
        />
    );
};

export default SparklesCursor;
