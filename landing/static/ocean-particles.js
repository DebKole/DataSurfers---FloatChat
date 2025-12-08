document.addEventListener('DOMContentLoaded', function() {
    // Create canvas
    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '0';
    canvas.style.opacity = '0.3';
    canvas.style.pointerEvents = 'none';
    document.body.prepend(canvas);

    // Setup canvas
    const ctx = canvas.getContext('2d');
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    // Set canvas size
    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    // Particle class
    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.size = Math.random() * 1.5 + 0.5; // Smaller particles
            this.speedX = Math.random() * 1 - 0.5;
            this.speedY = Math.random() * 1 - 0.5;
            this.color = `hsl(${Math.random() * 60 + 180}, 100%, 70%)`;
        }

        update(mouse) {
            // Move particles
            this.x += this.speedX;
            this.y += this.speedY;
            
            // Wrap around edges
            if (this.x > width + 10) this.x = -10;
            else if (this.x < -10) this.x = width + 10;
            if (this.y > height + 10) this.y = -10;
            else if (this.y < -10) this.y = height + 10;
            
            // Mouse interaction
            if (mouse.x && mouse.y) {
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 100) {
                    const angle = Math.atan2(dy, dx);
                    const force = (100 - distance) / 100;
                    this.x -= Math.cos(angle) * force * 0.5;
                    this.y -= Math.sin(angle) * force * 0.5;
                }
            }
        }

        draw() {
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // Create particles
    const particles = [];
    // Reduced density by increasing the divisor
    const particlesCount = Math.floor((width * height) / 18000);
    
    for (let i = 0; i < particlesCount; i++) {
        particles.push(new Particle());
    }

    // Mouse position
    const mouse = { x: null, y: null };
    
    window.addEventListener('mousemove', (e) => {
        mouse.x = e.x;
        mouse.y = e.y;
    });
    
    window.addEventListener('mouseout', () => {
        mouse.x = null;
        mouse.y = null;
    });

    // Animation loop
    function animate() {
        ctx.clearRect(0, 0, width, height);
        
        // Draw particles
        for (const particle of particles) {
            particle.update(mouse);
            particle.draw();
        }
        
        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 80) { // Reduced connection distance
                    ctx.beginPath();
                    // Reduced line opacity
                    ctx.strokeStyle = `rgba(100, 200, 255, ${(1 - distance / 80) * 0.5})`;
                    ctx.lineWidth = 0.5;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    // Start animation
    animate();
});
