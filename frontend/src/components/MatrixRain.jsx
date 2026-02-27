import { useEffect, useRef } from 'react';

/**
 * MatrixRain - A high-performance canvas-based matrix falling letters animation.
 */
export default function MatrixRain() {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;

        // Characters: Katakana, Digits, and Latin
        const chars = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789ABCDEF';
        const charArray = chars.split('');
        const fontSize = 16;
        const columns = Math.ceil(width / fontSize);

        // Initial drops (random starting Y positions to stagger)
        const drops = Array.from({ length: columns }, () => Math.random() * -100);

        const draw = () => {
            // Semi-transparent black background to create trail effect
            ctx.fillStyle = 'rgba(10, 14, 26, 0.1)';
            ctx.fillRect(0, 0, width, height);

            ctx.fillStyle = '#10b981'; // neon-green
            ctx.font = `${fontSize}px monospace`;

            for (let i = 0; i < drops.length; i++) {
                const text = charArray[Math.floor(Math.random() * charArray.length)];

                // Randomly highlight Some characters to white for "glitch" look
                if (Math.random() > 0.98) {
                    ctx.fillStyle = '#fff';
                } else {
                    ctx.fillStyle = '#10b981';
                }

                ctx.fillText(text, i * fontSize, drops[i] * fontSize);

                // Reset drop to top when it hits bottom or randomly
                if (drops[i] * fontSize > height && Math.random() > 0.975) {
                    drops[i] = 0;
                }

                drops[i] += 0.8; // Speed controlled by increment
            }
        };

        const interval = setInterval(draw, 33);

        const handleResize = () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
            // Recalculate drops if needed, but keeping existing is usually fine
        };

        window.addEventListener('resize', handleResize);

        return () => {
            clearInterval(interval);
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-0 opacity-20"
            style={{ filter: 'blur(0.5px)' }}
        />
    );
}
