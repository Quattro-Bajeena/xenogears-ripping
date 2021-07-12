import * as THREE from "https://threejs.org/build/three.module.js";
import { OrbitControls } from "https://threejs.org/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "https://threejs.org/examples/jsm/loaders/GLTFLoader.js";


let camera, scene, renderer, map, controls;
const parent = document.getElementById("render");

init();
render();

function init(){

    const width = parent.clientWidth;
    const height = parent.clientHeight;

    renderer = new THREE.WebGLRenderer();
    renderer.setPixelRatio( window.devicePixelRatio );
    renderer.setSize( width, height );
    renderer.outputEncoding = THREE.sRGBEncoding;
    parent.appendChild(renderer.domElement);

    camera = new THREE.PerspectiveCamera( 60, width / height, 10, 20000 );
    camera.position.set( 4500, 1000, 800 );
    camera.lookAt( 0, 0, 0 );

    scene = new THREE.Scene();

    const loadingManager = new THREE.LoadingManager(function(){
        scene.add(map);
    })


    const loader = new GLTFLoader( loadingManager);
    const map_url = "/Maps/Converted/level1.glb";
    loader.load(map_url, function(gltf){
        //console.log(gltf);
        
        for(const object of gltf.scene.children){
            
            object.traverse(function(child){
                if(child instanceof THREE.Mesh){

                    // if(child.material.map != null){
                    //     child.material.map.magFilter = THREE.NearestFilter;
                    // }

                    child.material.emissive = new THREE.Color( 1,1,1);
                    child.material.emissiveMap = child.material.map;
                    child.material.emissiveIntensity = 1;
                    //child.material.map = null;

                }

            });
        }
        map = gltf.scene;
        render();
    });


    controls = new OrbitControls( camera, renderer.domElement );
    //controls.addEventListener( 'change', render ); // use if there is no animation loop
    controls.minDistance = 1000;
    controls.maxDistance = 7000;
    controls.target.set( 0, 0, 0 );
    controls.update();

    window.addEventListener( 'resize', onWindowResize );
    
    render();
}


function onWindowResize() {
    const width = parent.clientWidth;
    const height = parent.clientHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize( width, height );
    render();
    
}


function render() {
    requestAnimationFrame( render );
    resizeCanvasToDisplaySize();
    renderer.render( scene, camera );
    
}

function resizeCanvasToDisplaySize() {
    const canvas = renderer.domElement;
    // look up the size the canvas is being displayed
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
  
    // adjust displayBuffer size to match
    if (canvas.width !== width || canvas.height !== height) {
      // you must pass false here or three.js sadly fights the browser
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
  
      // update any render target sizes here
    }
  }

