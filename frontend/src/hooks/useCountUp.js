import { useState, useEffect, useRef } from 'react';

/**
 * Hook that animates a number counting up from 0 to a target value.
 * @param {number} end - The target value to count up to.
 * @param {number} duration - Duration of the animation in milliseconds.
 * @param {string} suffix - Optional suffix to append (e.g., '%', 'k')
 * @param {string} prefix - Optional prefix to prepend (e.g., '$')
 * @param {boolean} startOnMount - Whether to start immediately on mount.
 * @returns {string} The current animated value as a formatted string.
 */
export function useCountUp(end, duration = 2000, { suffix = '', prefix = '', decimals = 0 } = {}) {
    const [count, setCount] = useState(0);
    const frameRef = useRef(null);
    const startTimeRef = useRef(null);

    useEffect(() => {
        if (typeof end !== 'number' || isNaN(end)) return;

        const animate = (timestamp) => {
            if (!startTimeRef.current) startTimeRef.current = timestamp;
            const progress = Math.min((timestamp - startTimeRef.current) / duration, 1);

            // Ease out cubic for a satisfying deceleration
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = eased * end;

            setCount(current);

            if (progress < 1) {
                frameRef.current = requestAnimationFrame(animate);
            }
        };

        frameRef.current = requestAnimationFrame(animate);

        return () => {
            if (frameRef.current) {
                cancelAnimationFrame(frameRef.current);
            }
        };
    }, [end, duration]);

    const formatted = decimals > 0
        ? count.toFixed(decimals)
        : Math.round(count).toLocaleString();

    return `${prefix}${formatted}${suffix}`;
}

export default useCountUp;
