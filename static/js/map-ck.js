/**
 * Created with IntelliJ IDEA.
 * User: hstrauss
 * Date: 7/7/13
 * Time: 10:10 AM
 * To change this template use File | Settings | File Templates.
 */function viewDetails(e){$("#map_item_results").empty();$("#map_search_results").empty();$.getJSON("/data/connections.json",function(e){console.log(e);if(e.meta.status==200&&e.response.total_connections==1){$("#map_item_results").append('<div id="map_item_results_cont">');$("#map_item_results_cont").append('<img id="map_item_primary" src="'+e.response.connections[0].primary_cont_url+'" alt="Smiley face">');$("#map_item_results_cont").append('<div id="map_item_header"></d>');$("#map_item_results_cont").append('<img id="map_item_person" src="'+e.response.connections[0].person_picture+'" alt="Smiley face" >');$("#map_item_results_cont").append('<p id="map_item_title">'+e.response.connections[0].title+"</p>");$("#map_item_results_cont").append('<p id="map_item_stage">'+e.response.connections[0].connection.stage+"</p>");$("#map_item_results_cont").append('<p id="map_item_summary">'+e.response.connections[0].summary+"</p>");$("#map_item_results_cont").append('<img id="map_item_tweet_url" src="'+e.response.connections[0].tweet_url+'" alt="Smiley face" height="42" width="42">');$("#map_item_results_cont").append('<img id="map_item_fb_url" src="'+e.response.connections[0].fb_url+'" alt="Smiley face" height="42" width="42">');$("#map_item_results_cont").append('<p id="map_item_blog_url">'+e.response.connections[0].blog_url+"</p>");$("#map_item_results_cont").append('<p id="map_item_post_url">'+e.response.connections[0].post_url+"</p>")}})}function addSearchTypeAhead(e){var t=[],n=[],r=[];$("#map_search_results").empty();$.getJSON("/data/search.json",function(e){console.log(e);if(e.meta.status==200){$("#map_search_results").append('<table id="map_search_results_search">');for(var i=0;i<e.response.total_results;i++)e.response.results[i].type=="give"?t.push(i):e.response.results[i].type=="get"?n.push(i):e.response.results[i].type=="person"&&r.push(i);if(t.length>0)for(var s=0;s<t.length;s++){var o=t[s],u=e.response.results[o];s==0?$("#map_search_results_search").append('<tr class="search_table_item"><a><td class="list_cat_title">Give</td><td class="search_result_list_item" data-id="'+u.connection.id+'" data-lat="'+u.latitude+'" data-lng="'+u.longitude+'"><p class="search_result">'+u.title+'</p><p class="search_person_name">'+u.person_name+"</p></td></a></tr>"):$("#map_search_results_search").append('<tr class="search_table_item"><a><td></td><td data-id="'+u.connection.id+'" data-lat="'+u.latitude+'" data-lng="'+u.longitude+'" class="search_result_list_item"><p class="search_result">'+u.title+'</p><p class="search_person_name">'+u.person_name+"</p></td></a></tr>")}if(n.length>0)for(var s=0;s<n.length;s++){var o=n[s],u=e.response.results[o];s==0?$("#map_search_results_search").append('<tr class="search_table_item"><a><td class="list_cat_title">Get</td><td class="search_result_list_item" data-id="'+u.connection.id+'" data-lat="'+u.latitude+'" data-lng="'+u.longitude+'"><p class="search_result">'+u.title+'</p><p class="search_person_name">'+u.person_name+"</p></td></a></tr>"):$("#map_search_results_search").append('<tr class="search_table_item"><a><td></td><td class="search_result_list_item" data-id="'+u.connection.id+'" data-lat="'+u.latitude+'" data-lng="'+u.longitude+'"><p class="search_result">'+u.title+'</p><p class="search_person_name">'+u.person_name+"</p></td></a></tr>")}if(r.length>0)for(var s=0;s<r.length;s++){var o=r[s],u=e.response.results[o];s==0?$("#map_search_results_search").append('<tr class="search_table_item"><a><td class="list_cat_title">People</td><td class="search_result_list_item"><p class="search_result">'+u.person_name+"</p></td></a></tr>"):$("#map_search_results_search").append('<tr class="search_table_item"><a><td></td><td class="search_result_list_item"><p class="search_result">'+u.person_name+"</p></td></a></tr>")}}$(".search_result_list_item").click(function(){connection.map.setView([this.dataset.lat,this.dataset.lng],10);viewDetails(this.dataset.id)})})}var connection=connection||{};connection.map=L.mapbox.map("map","straussh.map-lrzsy60w",{zoomControl:!1});(new L.Control.Zoom({position:"bottomright"})).addTo(connection.map);connection.map.markerLayer.on("layeradd",function(e){var t=e.layer,n=t.feature,r='<div class="popup">   <p class="map_popup_title">'+n.properties.title+"</p>"+'   <p class="map_popup_location">'+n.properties.loc_name+"</p>"+"</div>";t.bindPopup(r,{closeButton:!1})});connection.list_all=function(){var e=function(){gapi.client.alittlecloser.connections.list().execute(function(e){console.log(e)})};gapi.client.load("alittlecloser","v1",e,alittlecloser.apiRoot)};connection.map.markerLayer.loadURL("/data/example-single.geojson");connection.map.markerLayer.on("mouseover",function(e){e.layer.openPopup()});connection.map.markerLayer.on("mouseout",function(e){e.layer.closePopup()});connection.map.markerLayer.on("click",function(e){viewDetails(e.layer.feature.properties["person-id"]);e.layer.openPopup()});connection.map.setView([40,-98],5);