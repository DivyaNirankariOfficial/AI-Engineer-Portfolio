import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

const HeroCanvas = () => {
  const mountRef = useRef(null);

  useEffect(() => {
    let width = mountRef.current.clientWidth;
    let height = mountRef.current.clientHeight;
    let frameId;

    // Scene
    const scene = new THREE.Scene();

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 5;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Optimize performance
    mountRef.current.appendChild(renderer.domElement);

    // Group to hold the cloud
    const group = new THREE.Group();
    scene.add(group);

    // Particles Data
    const particleCount = 200;
    const maxDistance = 1.2; // connection distance
    const particlePositions = new Float32Array(particleCount * 3);
    const particleData = [];

    // Distribute points in a sphere
    const radius = 3.5;
    for (let i = 0; i < particleCount; i++) {
      const r = radius * Math.cbrt(Math.random());
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);
      
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);

      particlePositions[i * 3] = x;
      particlePositions[i * 3 + 1] = y;
      particlePositions[i * 3 + 2] = z;

      particleData.push({
        velocity: new THREE.Vector3(-0.005 + Math.random() * 0.01, -0.005 + Math.random() * 0.01, -0.005 + Math.random() * 0.01),
        numConnections: 0
      });
    }

    // Points
    const pMaterial = new THREE.PointsMaterial({
      color: 0x5c4b78,
      size: 0.04,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });
    
    const pGeometry = new THREE.BufferGeometry();
    pGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const pointCloud = new THREE.Points(pGeometry, pMaterial);
    group.add(pointCloud);

    // Lines
    const linePositions = new Float32Array(particleCount * particleCount * 3);
    const lineColors = new Float32Array(particleCount * particleCount * 3);
    const lGeometry = new THREE.BufferGeometry();
    
    lGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3).setUsage(THREE.DynamicDrawUsage));
    lGeometry.setAttribute('color', new THREE.BufferAttribute(lineColors, 3).setUsage(THREE.DynamicDrawUsage));
    
    const lMaterial = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.15,
      blending: THREE.AdditiveBlending
    });
    const linesMesh = new THREE.LineSegments(lGeometry, lMaterial);
    group.add(linesMesh);

    // Mouse Interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;
    
    const onMouseMove = (event) => {
      // normalized coordinates -1 to +1
      mouseX = (event.clientX - window.innerWidth / 2) / (window.innerWidth / 2);
      mouseY = (event.clientY - window.innerHeight / 2) / (window.innerHeight / 2);
    };
    window.addEventListener('mousemove', onMouseMove);

    // Animation Loop
    const animate = () => {
      let vertexpos = 0;
      let colorpos = 0;
      let numConnected = 0;

      // Update particles
      for (let i = 0; i < particleCount; i++)
        particleData[i].numConnections = 0;

      for (let i = 0; i < particleCount; i++) {
        const particleDataB = particleData[i];
        
        // Move particle
        particlePositions[i * 3] += particleDataB.velocity.x;
        particlePositions[i * 3 + 1] += particleDataB.velocity.y;
        particlePositions[i * 3 + 2] += particleDataB.velocity.z;
        
        // Bounce off sphere boundary
        const v = new THREE.Vector3(particlePositions[i * 3], particlePositions[i * 3 + 1], particlePositions[i * 3 + 2]);
        if (v.length() > radius) {
          particleDataB.velocity.x = -particleDataB.velocity.x;
          particleDataB.velocity.y = -particleDataB.velocity.y;
          particleDataB.velocity.z = -particleDataB.velocity.z;
        }

        // Check distance for lines
        for (let j = i + 1; j < particleCount; j++) {
          const particleDataA = particleData[j];

          const dx = particlePositions[i * 3] - particlePositions[j * 3];
          const dy = particlePositions[i * 3 + 1] - particlePositions[j * 3 + 1];
          const dz = particlePositions[i * 3 + 2] - particlePositions[j * 3 + 2];
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

          if (dist < maxDistance) {
            particleDataB.numConnections++;
            particleDataA.numConnections++;

            const alpha = 1.0 - dist / maxDistance;

            linePositions[vertexpos++] = particlePositions[i * 3];
            linePositions[vertexpos++] = particlePositions[i * 3 + 1];
            linePositions[vertexpos++] = particlePositions[i * 3 + 2];

            linePositions[vertexpos++] = particlePositions[j * 3];
            linePositions[vertexpos++] = particlePositions[j * 3 + 1];
            linePositions[vertexpos++] = particlePositions[j * 3 + 2];

            // Color gradient based on distance
            // Base color: #5c4b78 (R=0.36, G=0.29, B=0.47)
            const r = 0.36 * alpha;
            const g = 0.29 * alpha;
            const b = 0.47 * alpha;

            lineColors[colorpos++] = r;
            lineColors[colorpos++] = g;
            lineColors[colorpos++] = b;

            lineColors[colorpos++] = r;
            lineColors[colorpos++] = g;
            lineColors[colorpos++] = b;
            
            numConnected++;
          }
        }
      }

      pGeometry.attributes.position.needsUpdate = true;
      lGeometry.setDrawRange(0, numConnected * 2);
      lGeometry.attributes.position.needsUpdate = true;
      lGeometry.attributes.color.needsUpdate = true;

      // Mouse Parallax Interaction
      targetX = mouseX * 0.5;
      targetY = mouseY * 0.5;
      
      group.rotation.x += 0.001;
      group.rotation.y += 0.002;
      
      // smooth interpolation towards target rotation
      scene.rotation.x += (targetY - scene.rotation.x) * 0.05;
      scene.rotation.y += (targetX - scene.rotation.y) * 0.05;

      renderer.render(scene, camera);
      frameId = window.requestAnimationFrame(animate);
    };

    const handleResize = () => {
      if (!mountRef.current) return;
      width = mountRef.current.clientWidth;
      height = mountRef.current.clientHeight;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    window.addEventListener('resize', handleResize);
    animate();

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', onMouseMove);
      window.cancelAnimationFrame(frameId);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      pGeometry.dispose();
      pMaterial.dispose();
      lGeometry.dispose();
      lMaterial.dispose();
      renderer.dispose();
    };
  }, []);

  return <div ref={mountRef} className="w-full h-full" />;
};

export default HeroCanvas;
