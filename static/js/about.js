document.addEventListener("DOMContentLoaded", function () {
    // Create torch element
    const torch = document.createElement("div");
    torch.className = "cursor-torch";
    document.body.appendChild(torch);

    // Variables for smooth movement
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let torchX = mouseX;
    let torchY = mouseY;
    const ease = 0.1;

    // Set initial position
    torch.style.left = `${torchX}px`;
    torch.style.top = `${torchY}px`;

    // Track mouse movement
    document.addEventListener("mousemove", function (e) {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    // Smooth animation loop
    function animate() {
        // Calculate distance to move
        let dx = mouseX - torchX;
        let dy = mouseY - torchY;

        // Apply easing
        torchX += dx * ease;
        torchY += dy * ease;

        // Update torch position
        torch.style.left = `${torchX}px`;
        torch.style.top = `${torchY}px`;

        requestAnimationFrame(animate);
    }

    // Start animation
    animate();

    // Handle mouse enter/leave
    document.addEventListener("mouseenter", function () {
        torch.style.opacity = "1";
    });

    document.addEventListener("mouseleave", function () {
        torch.style.opacity = "0";
    });

    // Handle window resize
    window.addEventListener("resize", function () {
        // Keep torch centered if mouse is off screen
        mouseX = Math.max(0, Math.min(mouseX, window.innerWidth));
        mouseY = Math.max(0, Math.min(mouseY, window.innerHeight));
    });

    // Make sure torch is initially hidden
    torch.style.opacity = "0";

    // Add slight delay before showing to prevent initial flash
    setTimeout(() => {
        torch.style.transition = "opacity 0.3s ease";
    }, 100);
});
