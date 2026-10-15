const ORB_SIZE = 400;
const PARTICLES_PER_FRAME = 6;
const SPHERE_RADIUS_FACTOR = 0.35;
const PROJECTION_FACTOR = 0.78;
const ZERO_ALPHA_DEPTH = -900;
const PARTICLE_BASE_RADIUS = 1.35;
const ROTATION_STEP = (2 * Math.PI) / 1600;
const RANDOM_ACCELERATION = 0.024;

window.addEventListener("load", () => {
  initializeOrbAnimation();
  initializeStarsCanvas();
}, false);

function initializeOrbAnimation() {
  if (!window.Modernizr || !Modernizr.canvas) {
    return;
  }

  const canvas = document.getElementById("canvasOne");
  if (!canvas) {
    return;
  }

  const context = canvas.getContext("2d");
  if (!context) {
    return;
  }

  const particleList = {};
  const recycleBin = {};
  let animationFrameId = null;
  let turnAngle = 0;
  let displayWidth = 0;
  let displayHeight = 0;
  let focalLength = 0;
  let projectionCenterX = 0;
  let projectionCenterY = 0;
  let zMax = 0;
  let sphereRadius = 0;
  let sphereCenterZ = 0;

  function resizeCanvas() {
    const pixelRatio = window.devicePixelRatio || 1;
    const targetSize = Math.min(ORB_SIZE, Math.max(260, window.innerWidth * 0.46));

    canvas.style.width = `${targetSize}px`;
    canvas.style.height = `${targetSize}px`;
    canvas.width = Math.round(targetSize * pixelRatio);
    canvas.height = Math.round(targetSize * pixelRatio);

    context.setTransform(1, 0, 0, 1, 0, 0);
    context.scale(pixelRatio, pixelRatio);

    displayWidth = targetSize;
    displayHeight = targetSize;
    focalLength = targetSize * PROJECTION_FACTOR;
    projectionCenterX = displayWidth / 2;
    projectionCenterY = displayHeight / 2;
    zMax = focalLength - 2;
    sphereRadius = targetSize * SPHERE_RADIUS_FACTOR;
    sphereCenterZ = -3 - sphereRadius;
  }

  function addParticle(x, y, z, velocityX, velocityY, velocityZ) {
    let particle;

    if (recycleBin.first) {
      particle = recycleBin.first;
      recycleBin.first = particle.next || null;
      if (recycleBin.first) {
        recycleBin.first.prev = null;
      }
    } else {
      particle = {};
    }

    particle.x = x;
    particle.y = y;
    particle.z = z;
    particle.velX = velocityX;
    particle.velY = velocityY;
    particle.velZ = velocityZ;
    particle.accelX = 0;
    particle.accelY = 0;
    particle.accelZ = 0;
    particle.attack = 45;
    particle.hold = 50;
    particle.decay = 150;
    particle.initValue = 0;
    particle.holdValue = 1;
    particle.lastValue = 0;
    particle.alpha = 0;
    particle.age = 0;
    particle.dead = false;
    particle.stuckTime = 55 + Math.random() * 35;

    if (!particleList.first) {
      particle.prev = null;
      particle.next = null;
      particleList.first = particle;
      return particle;
    }

    particle.next = particleList.first;
    particle.prev = null;
    particleList.first.prev = particle;
    particleList.first = particle;
    return particle;
  }

  function recycleParticle(particle) {
    if (particleList.first === particle) {
      particleList.first = particle.next || null;
      if (particleList.first) {
        particleList.first.prev = null;
      }
    } else {
      if (particle.prev) {
        particle.prev.next = particle.next || null;
      }
      if (particle.next) {
        particle.next.prev = particle.prev || null;
      }
    }

    particle.prev = null;
    particle.next = recycleBin.first || null;
    if (recycleBin.first) {
      recycleBin.first.prev = particle;
    }
    recycleBin.first = particle;
  }

  function spawnParticles() {
    for (let index = 0; index < PARTICLES_PER_FRAME; index += 1) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const x = sphereRadius * Math.sin(phi) * Math.cos(theta);
      const y = sphereRadius * Math.sin(phi) * Math.sin(theta);
      const z = sphereRadius * Math.cos(phi);

      addParticle(
        x,
        y,
        sphereCenterZ + z,
        x * 0.0022,
        y * 0.0022,
        z * 0.0022,
      );
    }
  }

  function updateParticleAlpha(particle) {
    if (particle.age < particle.attack) {
      particle.alpha =
        ((particle.holdValue - particle.initValue) / particle.attack) * particle.age +
        particle.initValue;
      return;
    }

    if (particle.age < particle.attack + particle.hold) {
      particle.alpha = particle.holdValue;
      return;
    }

    if (particle.age < particle.attack + particle.hold + particle.decay) {
      particle.alpha =
        ((particle.lastValue - particle.holdValue) / particle.decay) *
          (particle.age - particle.attack - particle.hold) +
        particle.holdValue;
      return;
    }

    particle.dead = true;
  }

  function drawFrame() {
    spawnParticles();
    turnAngle = (turnAngle + ROTATION_STEP) % (Math.PI * 2);

    const sinAngle = Math.sin(turnAngle);
    const cosAngle = Math.cos(turnAngle);

    context.clearRect(0, 0, displayWidth, displayHeight);
    context.fillStyle = "rgba(0, 0, 0, 0.22)";
    context.fillRect(0, 0, displayWidth, displayHeight);

    let particle = particleList.first || null;
    while (particle) {
      const nextParticle = particle.next || null;
      particle.age += 1;

      if (particle.age > particle.stuckTime) {
        particle.velX += (Math.random() * 2 - 1) * RANDOM_ACCELERATION;
        particle.velY += (Math.random() * 2 - 1) * RANDOM_ACCELERATION;
        particle.velZ += (Math.random() * 2 - 1) * RANDOM_ACCELERATION;
        particle.x += particle.velX;
        particle.y += particle.velY;
        particle.z += particle.velZ;
      }

      const rotatedX = cosAngle * particle.x + sinAngle * (particle.z - sphereCenterZ);
      const rotatedZ =
        -sinAngle * particle.x + cosAngle * (particle.z - sphereCenterZ) + sphereCenterZ;
      const perspective = focalLength / (focalLength - rotatedZ);

      particle.projX = rotatedX * perspective + projectionCenterX;
      particle.projY = particle.y * perspective + projectionCenterY;

      updateParticleAlpha(particle);

      const outsideView =
        particle.projX < 0 ||
        particle.projX > displayWidth ||
        particle.projY < 0 ||
        particle.projY > displayHeight ||
        rotatedZ > zMax;

      if (outsideView || particle.dead) {
        recycleParticle(particle);
        particle = nextParticle;
        continue;
      }

      const depthAlpha = Math.max(0, Math.min(1, 1 - rotatedZ / ZERO_ALPHA_DEPTH));
      const finalAlpha = Math.max(0.04, depthAlpha * particle.alpha);
      const glowRadius = Math.max(0.9, perspective * PARTICLE_BASE_RADIUS);

      context.beginPath();
      context.fillStyle = `rgba(255, 255, 255, ${finalAlpha})`;
      if (finalAlpha > 0.6) {
        context.shadowColor = "rgba(255, 255, 255, 0.75)";
        context.shadowBlur = 4;
      } else {
        context.shadowBlur = 0;
      }
      context.arc(particle.projX, particle.projY, glowRadius, 0, Math.PI * 2, false);
      context.fill();

      particle = nextParticle;
    }
    context.shadowBlur = 0;

    animationFrameId = window.requestAnimationFrame(drawFrame);
  }

  resizeCanvas();
  drawFrame();

  window.addEventListener("resize", resizeCanvas);
  window.addEventListener("beforeunload", () => {
    if (animationFrameId !== null) {
      window.cancelAnimationFrame(animationFrameId);
    }
  });
}

function initializeStarsCanvas() {
  const canvas = document.getElementById("starsCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  let width = 0;
  let height = 0;
  let stars = [];
  const bursts = [];
  const meteors = [];
  const mouse = { x: -1000, y: -1000, radius: 130 };
  const STAR_COUNT = 150;

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
    initStars();
  }

  function initStars() {
    stars = [];
    for (let i = 0; i < STAR_COUNT; i++) {
      stars.push({
        x: Math.random() * width,
        y: Math.random() * height,
        baseSize: 0.7 + Math.random() * 1.8,
        twinkleSpeed: 0.015 + Math.random() * 0.03,
        twinklePhase: Math.random() * Math.PI * 2,
        baseAlpha: 0.25 + Math.random() * 0.55,
        vx: (Math.random() - 0.5) * 0.12,
        vy: (Math.random() - 0.5) * 0.12,
        color: Math.random() > 0.8 ? "rgba(220, 180, 255," : "rgba(255, 255, 255,"
      });
    }
  }

  window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  window.addEventListener("mouseleave", () => {
    mouse.x = -1000;
    mouse.y = -1000;
  });

  window.addEventListener("click", (e) => {
    for (let i = 0; i < 10; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 0.5 + Math.random() * 2.5;
      bursts.push({
        x: e.clientX,
        y: e.clientY,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: 1 + Math.random() * 2,
        alpha: 1,
        decay: 0.02 + Math.random() * 0.02
      });
    }
  });

  function draw() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      s.x += s.vx;
      s.y += s.vy;
      if (s.x < 0) s.x = width;
      if (s.x > width) s.x = 0;
      if (s.y < 0) s.y = height;
      if (s.y > height) s.y = 0;

      s.twinklePhase += s.twinkleSpeed;
      const twinkle = Math.sin(s.twinklePhase) * 0.35;
      let alpha = Math.max(0.08, Math.min(1, s.baseAlpha + twinkle));
      let size = s.baseSize;

      const dx = mouse.x - s.x;
      const dy = mouse.y - s.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < mouse.radius) {
        const factor = 1 - dist / mouse.radius;
        alpha = Math.min(1, alpha + factor * 0.6);
        size = s.baseSize + factor * 1.4;

        s.x -= (dx / dist) * 0.8 * factor;
        s.y -= (dy / dist) * 0.8 * factor;

        if (dist < 80) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(197, 47, 255, ${0.28 * (1 - dist / 80)})`;
          ctx.lineWidth = 0.6;
          ctx.moveTo(s.x, s.y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.stroke();
        }
      }

      ctx.beginPath();
      ctx.fillStyle = `${s.color} ${alpha})`;
      if (alpha > 0.7) {
        ctx.shadowColor = s.color.includes("220") ? "rgba(197, 47, 255, 0.8)" : "rgba(255, 255, 255, 0.8)";
        ctx.shadowBlur = 4;
      } else {
        ctx.shadowBlur = 0;
      }
      ctx.arc(s.x, s.y, size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;

    for (let i = bursts.length - 1; i >= 0; i--) {
      const b = bursts[i];
      b.x += b.vx;
      b.y += b.vy;
      b.alpha -= b.decay;
      if (b.alpha <= 0) {
        bursts.splice(i, 1);
        continue;
      }
      ctx.beginPath();
      ctx.fillStyle = `rgba(255, 255, 255, ${b.alpha})`;
      ctx.arc(b.x, b.y, b.size, 0, Math.PI * 2);
      ctx.fill();
    }

    if (Math.random() < 0.007 && meteors.length < 2) {
      meteors.push({
        x: Math.random() * (width * 0.8),
        y: -30,
        length: 70 + Math.random() * 60,
        speed: 7 + Math.random() * 5,
        angle: Math.PI / 4 + (Math.random() - 0.5) * 0.2,
        alpha: 1,
      });
    }

    for (let i = meteors.length - 1; i >= 0; i--) {
      const m = meteors[i];
      m.x += Math.cos(m.angle) * m.speed;
      m.y += Math.sin(m.angle) * m.speed;
      m.alpha -= 0.016;
      if (m.alpha <= 0 || m.x > width + 100 || m.y > height + 100) {
        meteors.splice(i, 1);
        continue;
      }
      const tailX = m.x - Math.cos(m.angle) * m.length;
      const tailY = m.y - Math.sin(m.angle) * m.length;
      const grad = ctx.createLinearGradient(tailX, tailY, m.x, m.y);
      grad.addColorStop(0, "rgba(168, 85, 247, 0)");
      grad.addColorStop(0.7, `rgba(192, 132, 252, ${m.alpha * 0.6})`);
      grad.addColorStop(1, `rgba(255, 255, 255, ${m.alpha})`);
      ctx.beginPath();
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.3;
      ctx.moveTo(tailX, tailY);
      ctx.lineTo(m.x, m.y);
      ctx.stroke();
    }

    requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener("resize", resize);
  draw();
}
