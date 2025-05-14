document.getElementById('submitBtn').addEventListener('click', function () {
    const roll = parseFloat(document.getElementById('roll').value);
    const pitch = parseFloat(document.getElementById('pitch').value);
    const yaw = parseFloat(document.getElementById('yaw').value);
    const thrust = parseFloat(document.getElementById('thrust').value);

    // Update the output section
    document.getElementById('rpy-output').innerHTML = `Roll: ${roll}° | Pitch: ${pitch}° | Yaw: ${yaw}° | Thrust: ${thrust}`;

    // Call the function to update the 3D visualization
    update3DMap(roll, pitch, yaw, thrust);
});

function update3DMap(roll, pitch, yaw, thrust) {
    // Basic 3D setup using Three.js
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 400, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, 400);
    document.getElementById('3d-map').appendChild(renderer.domElement);

    // Create a simple sphere to represent the UAV
    const geometry = new THREE.SphereGeometry(1, 32, 32);
    const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
    const sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);

    // Apply RPYT to the sphere
    sphere.rotation.x = THREE.MathUtils.degToRad(roll);
    sphere.rotation.y = THREE.MathUtils.degToRad(pitch);
    sphere.rotation.z = THREE.MathUtils.degToRad(yaw);

    // Set camera position
    camera.position.z = 5;

    // Animate the scene
    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();
}
