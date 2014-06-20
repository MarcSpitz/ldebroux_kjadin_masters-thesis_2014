
function fillDiv(divName, jsonFile, width, height) {

  var w = width,
      h = height,
      fill = d3.scale.category20();

  var nodeRadius = 12;
  var nodeDistance = 40;
  var charge = -125;

  var vis = d3.select("#chart")
    .append("svg:svg")
      .attr("width", w)
      .attr("height", h);

  d3.json(jsonFile, function(json) {

    console.log(json)

    var force = d3.layout.force()
        .charge(charge)
        .linkDistance(nodeDistance)
        .nodes(json.nodes)
        .links(json.links)
        .size([w, h])
        .start();

    console.log(json.links)

  // <marker id="triangle"
  //       viewBox="0 0 10 10" refX="0" refY="5" 
  //       markerUnits="strokeWidth"
  //       markerWidth="4" markerHeight="3"
  //       orient="auto">
  //       <path d="M 0 0 L 10 5 L 0 10 z" />
  //     </marker>
  //   <line x1="100" y1="50.5" x2="300" y2="50.5" marker-end="url(#triangle)" stroke="black" stroke-width="10"/>

    var marker = vis.selectAll("marker")
      .data(["normal"])
    .enter().append("svg:marker")
      .attr("id", function(d) { return d; })
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", nodeRadius*2.1)
      .attr("refY", 0)
      .attr("markerWidth", 4)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
    .append("svg:path")
      .attr("d", "M0,-5L10,0L0,5")
    ;

    var path = vis.selectAll("path.link")
      .data(json.links)
      .enter().append("svg:path")
      .attr("class", "link")
      .attr("marker-end", "url(#normal)")
      ;

    var node = vis.selectAll("circle.node")
        .data(json.nodes)
      .enter().append("svg:circle")
        // .attr("class", "node")
        .attr("class", function(d) { return "node " + d.type; })
        .attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; })
        .attr("r", nodeRadius)
        .call(force.drag);

    var text = vis.selectAll("text")
        .data(json.nodes)
      .enter().append("svg:text")
        .attr("class", "circletext")
        .attr("x", 0)
        .attr("y", "0.31em")
        .attr("text-anchor", "middle")
        .attr("fill", "#FFFFFF")
        .text(function(d) { return d.name; });

    // var legend = vis.append("g")
    //   .attr("class", "legend")
    //   .attr("x", w/2)
    //   .attr("y", h/2)
    //   .attr("height", 100)
    //   .attr("width", 100);

    // legend.append("rect")
    //   .attr("x", w/2)
    //   .attr("y", h/2)
    //   .attr("width", 10)
    //   .attr("height", 10)
    //   // .attr("fill", "gray")
    //   ;

    // legend.append("text")
    //   .attr("x", w/2)
    //   .attr("y", h/2)
    //   .text("DKSDKAKSDKASDKADASKDKAKSDAKSDKASDKAS");

    // infoDict = dict(weight = T.weight, 
    //                 clients = len(T.C),
    //                 edges = len(T.number_of_edges()),
    //                 avgWeight = avgWeight

    console.log(json.treeInfo);

    // legend = vis.append("g")
    //     .data(json.treeInfo)
    //   .enter().append("svg:text")
    //     .attr("x", w/2)
    //     .attr("y", h/2)
    //     // .attr("text-anchor", "middle")
    //     // .text(function(d) { 
    //     //   var str = "nb clients = " + d.clients + "\n"
    //     //           + "nb edges   = " + d.edges   + "\n"
    //     //           + "weight     = " + d.weight  + "\n"
    //     //           + "avgWeight  = " + d.avgWeight;
    //     //   return str; 
    //     // })
    //     .text("A?SDFADJASDASJDAKSDJASKDAJ")
    //     ;


    textdy = "1.2em";
    legendX = 0;
    legendY = textdy;

    function fillLegend(legend) {
      
      legend.append("svg:tspan")
            .attr("x", legendX)
            .attr("dy", textdy)
            .text("average weight  = " + json.treeInfo.avgWeight);
      legend.append("svg:tspan")
            .attr("x", legendX)
            .attr("dy", textdy)
            .text("weight     = " + json.treeInfo.weight);     
      legend.append("svg:tspan")
            .attr("x", legendX)
            .attr("dy", textdy)
            .text("nb clients = " + json.treeInfo.clients);
      legend.append("svg:tspan")
            .attr("x", legendX)
            .attr("dy", textdy)
            .text("nb edges   = " + json.treeInfo.edges);
      
      
    }
    legend = vis.append("svg:text")
        .attr("x", legendX)
        .attr("y", legendY)
        .attr("class", "legend")
        // .attr("text-anchor", "middle")
        ;

    fillLegend(legend);
    


    // tooltips show node name
    // node.append("svg:title")
    //     .text(function(d) { return d.name; });

    vis.style("opacity", 1e-6)
      .transition()
        .duration(1000)
        .style("opacity", 1);

    function linkArc(d) {
      var dx = d.target.x - d.source.x,
          dy = d.target.y - d.source.y,
          dr = Math.sqrt(dx * dx + dy * dy);
      return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
    }

    function linkStraight(d) {
      var dx = d.target.x - d.source.x,
          dy = d.target.y - d.source.y,
          dr = Math.sqrt(dx * dx + dy * dy);
      // return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,5 " + d.target.x + "," + d.target.y;
      return "M" + d.source.x + "," + d.source.y + "," + d.target.x + "," + d.target.y;
    }

    function transform(d) {
      return "translate(" + d.x + "," + d.y + ")";
    }

    function tick() {
      // link
      //     .attr("x1", function(d) { return d.source.x; })
      //     .attr("y1", function(d) { return d.source.y; })
      //     .attr("x2", function(d) { return d.target.x; })
      //     .attr("y2", function(d) { return d.target.y; })
      //     ;

      path
          .attr("d", linkStraight);

      node
          .attr("cx", function(d) { return d.x; })
          .attr("cy", function(d) { return d.y; })
          // .attr("transform", transform)
          ;

      text
          .attr("transform", transform);
    }

    force.on("tick", tick);
  });

}