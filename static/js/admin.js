function loadAdminMap(map_filter_obj){
    map_filter_obj.lat = typeof map_filter_obj.lat !== 'undefined' ? map_filter_obj.lat : 40;
    map_filter_obj.lng = typeof map_filter_obj.lng !== 'undefined' ? map_filter_obj.lng : -98;
    map_filter_obj.node_id = typeof map_filter_obj.node_id !== 'undefined' ? map_filter_obj.node_id : "";
    map_filter_obj.zoom = typeof map_filter_obj.zoom !== 'undefined' ? map_filter_obj.zoom : 4;
    alittlecloser.admin_map = L.mapbox.map('admin_map', 'straussh.map-e6qp7fvc', { zoomControl: false }).addControl(L.mapbox.geocoderControl('straussh.map-lrzsy60w'));
    alittlecloser.admin_map.setView([map_filter_obj.lat, map_filter_obj.lng], map_filter_obj.zoom);
    new L.Control.Zoom({ position: 'topleft' }).addTo(alittlecloser.admin_map);
    featureGroup = L.featureGroup().addTo(alittlecloser.admin_map);
    drawControl = new L.Control.Draw({
        position: 'topleft',
        draw: {
            polyline:false,
            polygon: false,
            circle: false,
            rectangle: false
        },
        edit: {
            featureGroup: featureGroup
        }
    }).addTo(alittlecloser.admin_map);
    alittlecloser.admin_map.on('draw:created', function (e) {
        featureGroup = L.featureGroup().addTo(alittlecloser.admin_map);

        var type = e.layerType,
            layer = e.layer;

        if (type === 'marker') {

            alittlecloser.admin_lat = e.layer._latlng.lat;
            alittlecloser.admin_lng = e.layer._latlng.lng;
            $('#lat').val(alittlecloser.route_point_lat)
            $('#lng').val(alittlecloser.route_point_lng)
            // Do whatever else you need to. (save to db, add to map etc)
            alittlecloser.admin_map.addLayer(layer);
            alittlecloser.current_layer = layer;

            $('#myModal').modal({
                show:true
            })
        }


    });




};
