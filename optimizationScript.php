<?php


if ($_GET['fpga']) {
        $x = $_GET['fpga'];
        $y = file_get_contents("js/fpgas/data2.json");

        $data = json_decode($y,true);



        
        
     /*   foreach ($data['blocks'] as $item) {
           $rsc = new Resoruce($item['y'], $item['x'],$item['t']);
           $fpga->addResource($rsc);
        }*/
    
        echo $y;

          
 
}

if ($_POST['optimize']) {
    $json = $_POST['optimize'];
    $data = json_decode($json,true);
    file_put_contents("floorplanner/floorplanner/problem.json", $json);
    $tmp = exec("python floorplanner/floorplanner/exampleProblem.py",$my_output);
    
    
    $y = file_get_contents("js/result.json");

    echo $y;
 //   file_put_contents("aaaaa.txt", $json);
  
 //   echo $tmp;
}



/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

