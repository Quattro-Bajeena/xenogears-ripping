import * as THREE from "./three/build/three.module.js";
import { OrbitControls } from "./three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "./three/examples/jsm/loaders/GLTFLoader.js";


let container;
let camera, scene, renderer, map;

init();
render();

function init(){
    container = document.body;

    camera = new THREE.PerspectiveCamera( 60, window.innerWidth / window.innerHeight, 10, 20000 );
    camera.position.set( 4500, 1000, 800 );
    camera.lookAt( 0, 0, 0 );

    scene = new THREE.Scene();

    const loadingManager = new THREE.LoadingManager(function(){
        scene.add(map);
    })


    const loader = new GLTFLoader( loadingManager);
    const map_url = "/Maps/Converted/level729.glb";
    loader.load(map_url, function(gltf){
        //console.log(gltf);

        for(const object of gltf.scene.children){
            
            object.traverse(function(child){
                if(child instanceof THREE.Mesh){
                    if(child.material.map != null){
                        child.material.map.magFilter = THREE.NearestFilter;
                    }

                    child.material.emissive = new THREE.Color( 1,1,1);
                    child.material.emissiveMap = child.material.map;
                    child.material.emissiveIntensity = 1;
                    //child.material.map = null;

                }

            });
        }
        map = gltf.scene;
    });

    // const ambientLight = new THREE.AmbientLight( 0xcccccc, 2 );
    // scene.add( ambientLight );

    // const directionalLight = new THREE.DirectionalLight( 0xffffff, 0.8 );
    // directionalLight.position.set( 1, 1, 0 ).normalize();
    // scene.add( directionalLight );

    renderer = new THREE.WebGLRenderer();
    renderer.setPixelRatio( window.devicePixelRatio );
    renderer.setSize( window.innerWidth, window.innerHeight );
    renderer.outputEncoding = THREE.sRGBEncoding;

    
    container.appendChild( renderer.domElement );


    const controls = new OrbitControls( camera, renderer.domElement );
    controls.addEventListener( 'change', render ); // use if there is no animation loop
    controls.minDistance = 1000;
    controls.maxDistance = 7000;
    controls.target.set( 0, 0, 0 );
    controls.update();

    window.addEventListener( 'resize', onWindowResize );
}


function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize( window.innerWidth, window.innerHeight );
    render();
}


function render() {
    renderer.render( scene, camera );
}
