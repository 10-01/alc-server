/**
 *  Author:  @coto
 *  Function: insertParamToURL
 *  @param {String} key Parameter to insert into URL
 *  @param {String} value Value for new parameter
 *
 *  Insert parameters to the URL recognizing if it had parameters before.
 *  It will reload the page, it's likely better to store this until finished
 */


/** alittlecloser global namespace */
var alittlecloser = alittlecloser || {};

alittlecloser.apiRoot = '/_ah/api';



alittlecloser.connections = function(){
    var callback = function() {
        gapi.client.alittlecloser.connections.list({'limit':
            '5'}).execute(function(resp){
            alittlecloser.drawconnections(resp);
        });
    };
    gapi.client.load('alittlecloser', 'v1', callback, alittlecloser.apiRoot);
};

alittlecloser.extend_connections = function(cursor){
    var callback = function() {
        gapi.client.alittlecloser.connections.list({'limit':
            '5', 'cursor':cursor}).execute(function(resp){
                alittlecloser.drawconnections(resp);
            });
    };
    gapi.client.load('alittlecloser', 'v1', callback, alittlecloser.apiRoot);
};


alittlecloser.drawconnections = function(resp){
    for (var i=0,j=resp.connections.length;i<j;i++){
        if (resp.connections[i].title){
            $('#connection_holder').append($('<div/>', {'class': 'row', html: $('<div/>', {'class': 'col-md-12 col-xs-12 connection_item', html: $('<div/>', {'class': 'connection_listing', 'id': resp.connections[i].id, html: $('<a/>', {href: '/closer/' + resp.connections[i].id, html: $('<img class="col-md-12 col-xs-12" src="'+resp.connections[i].media[0].media_item_message[3].blob_key+'=s1280" alt="Primary Image"> ')})})})}));

            $('#'+resp.connections[i].id).append('<a href="/closer/'+resp.connections[i].id+'"><p class="item_title_conn">'+resp.connections[i].title+'</p></a>');
            $('#'+resp.connections[i].id).append('<div class="item_header_conn"></d>');
            $('#'+resp.connections[i].id).append('<div class="stage" id="stage_'+resp.connections[i].id+'">');
            if(resp.connections[i].connection_stage === "0"){
                $('#stage_'+resp.connections[i].id).append('<div class="fill_circle"></div>');
                $('#stage_'+resp.connections[i].id).append('<div class="empty_circle"></div>');
                $('#stage_'+resp.connections[i].id).append('<div class="empty_circle"></div>');
            }
            else if (resp.connections[i].connection_stage === "1"){
                $('#stage_'+resp.connections[i].id).append('<div class="fill_circle"></div>');
                $('#stage_'+resp.connections[i].id).append('<div class="fill_circle"></div>');
                $('#stage_'+resp.connections[i].id).append('<div class="empty_circle"></div>');
            }
            else{
                $('#stage_'+resp.connections[i].id).append('<div class="fill_circle"></div>');
                $('#stage_'+resp.connections[i].id).append('<div class="fill_circle"></div>');
                $('#stage_'+resp.connections[i].id).append('<div class="fill_circle"></div>');
            }

        }
    }
    $('#loading_div').hide();
    $('.spinner_id').hide();
    $('#connection_holder').fadeIn();
    if(resp.cursor != "No More Results"){
        $('#connection_holder').append('<div class="row"><div class="col-md-offset-5 col-md-4"><button type="button" id="' + resp.cursor + '" class="btn btn-large btn-danger load_more_results">Load More Connections</button></div></div>');
    }
};

alittlecloser.map = L.mapbox.map('addconnectionmap', 'straussh.map-lrzsy60w', { zoomControl: false }).addControl(L.mapbox.geocoderControl('straussh.map-lrzsy60w'));
alittlecloser.map.setView([40, -98], 3);
new L.Control.Zoom({ position: 'topright' }).addTo(alittlecloser.map);
featureGroup = L.featureGroup().addTo(alittlecloser.map);
drawControl = new L.Control.Draw({
    draw: {
        polyline: false,
        polygon: false,
        circle: false,
        rectangle: false
    },
    edit: {
        featureGroup: featureGroup,
        edit: false
    }
}).addTo(alittlecloser.map);

alittlecloser.map.on('draw:created', function (e) {
    featureGroup = L.featureGroup().addTo(alittlecloser.map);

    var type = e.layerType,
        layer = e.layer;

    if (type === 'marker') {
        if (alittlecloser.point_lat){
            alittlecloser.map.removeLayer(alittlecloser.current_layer);
        }
        else{
        }
        alittlecloser.point_lat = e.layer._latlng.lat;
        alittlecloser.point_lng = e.layer._latlng.lng;
        $('#map_next').removeAttr('disabled');
        $('#mapnext').click(function() {
            $("#formmapdiv").hide();
            $("#map_nav_controls").hide();
            $("#dropzonediv").fadeIn();
            $("#submit_nav").fadeIn();
            if (this !== event.target) return; // avoid infinite loop
        });
    }

    // Do whatever else you need to. (save to db, add to map etc)
    alittlecloser.map.addLayer(layer);
    alittlecloser.current_layer = layer;
});


$(document).ready(function() {

    /***** Get kind of device ****/
    var ua = navigator.userAgent;
    var checker = {
        ios: ua.match(/(iPhone|iPod|iPad)/),
        blackberry: ua.match(/BlackBerry/),
        android: ua.match(/Android/),
        mobile: ua.match(/(iPhone|iPod|iPad|BlackBerry|Android)/)
    };

    /* Fix Bar at top, except for iOS */
    var $win = $(window),
        $nav = $('.subnav'),
        $brand = $('.brand'),
        navTop = $('.subnav').length && $('.subnav').offset().top - 40,
        isFixed = 0;

    processScroll();

    $nav.on('click', function () {
        if (!isFixed) setTimeout(function () {  $win.scrollTop($win.scrollTop() - 47); }, 10);
    });

    $win.on('scroll', processScroll);

    function processScroll() {
        if(checker.ios) {
            return;
        }
        var scrollTop = $win.scrollTop();
        if (scrollTop >= navTop && !isFixed) {
            isFixed = 1;
            $nav.addClass('subnav-fixed');
            $brand.addClass('brand-fixed');
        } else if (scrollTop <= navTop && isFixed) {
            isFixed = 0;
            $nav.removeClass('subnav-fixed');
            $brand.removeClass('brand-fixed');
        }
    }

    /* Detects orientationchange event */
    // otherwise fall back to the resize event.
    // Fixing this bug: http://webdesignerwall.com/tutorials/iphone-safari-viewport-scaling-bug
    if (checker.mobile && checker.ios){
        var supportsOrientationChange = "onorientationchange" in window,
            orientationEvent = supportsOrientationChange ? "orientationchange" : "resize";

        window.addEventListener(orientationEvent, function() {
            $("body").css("width", "100%");
            //alert('HOLY ROTATING SCREENS BATMAN:' + window.orientation + " " + screen.width);
        }, false);

        var viewportmeta = document.querySelector('meta[name="viewport"]');
        if (viewportmeta) {
            viewportmeta.content = 'width=device-width, minimum-scale=1.0, maximum-scale=1.0, initial-scale=1.0';
            document.body.addEventListener('gesturestart', function () {
                viewportmeta.content = 'width=device-width, minimum-scale=0.25, maximum-scale=1';
            }, false);
        }

    }

    /* Change CSS definitión for collapse button */
    $('body').on('click.collapse.data-api', '[data-toggle=collapse]', function ( e ) {
        var $this = $(this), href
            , target = $this.attr('data-target')
                || e.preventDefault()
                || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, '') //strip for ie7
            , option = $(target).data('collapse') ? 'toggle' : $this.data();
        if(!$(target).hasClass("in")){
            $this.find("span").addClass("icon-chevron-down").removeClass("icon-chevron-up");
        }
        else {
            $this.find("span").removeClass("icon-chevron-down").addClass("icon-chevron-up");
        }
    });
});


//Connection Map Controls
function loadMap(map_filter_obj) {
    map_filter_obj.lat = typeof map_filter_obj.lat !== 'undefined' ? map_filter_obj.lat : 40;
    map_filter_obj.lng = typeof map_filter_obj.lng !== 'undefined' ? map_filter_obj.lng : -98;
    map_filter_obj.node_id = typeof map_filter_obj.node_id !== 'undefined' ? map_filter_obj.node_id : "";
    map_filter_obj.zoom = typeof map_filter_obj.zoom !== 'undefined' ? map_filter_obj.zoom : 5;

alittlecloser.connection_map = L.mapbox.map('map', 'straussh.map-lrzsy60w', { zoomControl: false });
new L.Control.Zoom({ position: 'bottomright' }).addTo(alittlecloser.connection_map);

alittlecloser.load_planned = function()
{
    var callback = function() {
    gapi.client.alittlecloser.locations.list({'type':"planned"}).execute(function(resp){
    console.log(resp);
    var line_points = [];
    for (var i=0,j=resp.locations.length;i<j;i++){
    line_points.push([resp.locations[i].latitude,resp.locations[i].longitude])
    };
var polyline_options = {
    color: '#7ab32f'
    };
var polyline = L.polyline(line_points, polyline_options).addTo(alittlecloser.connection_map);
alittlecloser.load_completed();
});
};
gapi.client.load('alittlecloser', 'v1', callback, alittlecloser.apiRoot);

};

    alittlecloser.load_completed = function()
{
    var callback = function() {
        gapi.client.alittlecloser.locations.list({'type':"completed"}).execute(function(resp){
            console.log(resp);
            var line_points = [];
            for (var i=0,j=resp.locations.length;i<j;i++){
                line_points.push([resp.locations[i].latitude,resp.locations[i].longitude])
            }
            var polyline_options = {
                color: '#d03b54'
            };
            var polyline = L.polyline(line_points, polyline_options).addTo(alittlecloser.connection_map);
        });
    };
    gapi.client.load('alittlecloser', 'v1', callback, alittlecloser.apiRoot);

};

alittlecloser.connection_list_all = function(){
    $('#map_spinner').show();
    var callback = function() {
        gapi.client.alittlecloser.connections.list({"limit":"400"}).execute(function(resp){
            alittlecloser.markers = new L.MarkerClusterGroup();
            $('#map_spinner').fadeOut();
            for (var i=0,j=resp.connections.length;i<j;i++){
                if (resp.connections[i].connection_stage === "0"){
                    alittlecloser.marker = L.marker(new L.LatLng(resp.connections[i].latitude, resp.connections[i].longitude), {
    //                    Adding necessary properties to the point

                        icon: L.mapbox.marker.icon({'marker-symbol':'bus','marker-color': 'D4472F'}),
                        point_id:resp.connections[i].id,
                        title: resp.connections[i].title

                    });
                }
                else{
                    alittlecloser.marker = L.marker(new L.LatLng(resp.connections[i].latitude, resp.connections[i].longitude), {
                        //                    Adding necessary properties to the point

                        icon: L.mapbox.marker.icon({'marker-symbol':'bus','marker-color': '6cc7b7'}),
                        point_id:resp.connections[i].id,
                        title: resp.connections[i].title

                    });

                }
                alittlecloser.marker.bindPopup(resp.connections[i].title);
                alittlecloser.markers.addLayer(alittlecloser.marker);
            }
            alittlecloser.load_completed();
            alittlecloser.load_planned();
            alittlecloser.markers.addTo(alittlecloser.connection_map.markerLayer);
            if(map_filter_obj.node_id!== ""){
                alittlecloser.viewDetails(map_filter_obj.node_id);
            }
        });
    };
    gapi.client.load('alittlecloser', 'v1', callback, alittlecloser.apiRoot);
};

alittlecloser.connection_one = function(connection_id){
    $('#map_spinner').fadeIn();
    var callback = function() {
        gapi.client.alittlecloser.connections.alittlecloser.connection.getdetails({'connection_id':connection_id}).execute(function(resp){
            return (resp);
            $('#map_spinner').fadeOut();
        });
    };
    gapi.client.load('alittlecloser', 'v1', callback, alittlecloser.apiRoot);
};

alittlecloser.connection_map.markerLayer.on('mouseover', function(e) {
    e.layer.openPopup();
});
alittlecloser.connection_map.markerLayer.on('mouseout', function(e) {
    e.layer.closePopup();
});

alittlecloser.connection_map.markerLayer.on('click',function(e) {
    alittlecloser.viewDetails(e.layer.options.point_id);
});



alittlecloser.connection_map.setView([map_filter_obj.lat, map_filter_obj.lng], map_filter_obj.zoom);
    alittlecloser.viewDetails = function(connection_id)
    {
        $('#map_spinner').show();
        $('#map_item_results').fadeOut(10);

        gapi.client.alittlecloser.connection.getdetails({'connection_id':connection_id}).execute(function(resp){
            $('#map_item_results').empty();
            $('#map_search_results').empty();
            $('#map_item_results').append('<div id="map_item_results_cont">');
            for (var i=0,j=resp.connection.media.length;i<j;i++){
                if(resp.connection.media[i].filename === resp.connection.primary_media){
                    if(resp.connection.media[i].media_item_message[0].file_cat==="image"){
                        $('#map_item_results_cont').append('<img id="map_item_primary" class="connection_item_image" data-filename="'+resp.connection.media[i].filename+'" src="'+resp.connection.media[i].media_item_message[2].blob_key+'" alt="Smiley face">');

                    }

                }
            }

            $('#map_item_results_cont').append('<a href="/closer/'+resp.connection.id+'"><p id="map_item_title">'+resp.connection.title.substring(0,40)+'</p></a>');
            $('#map_item_results_cont').append('<div id="map_item_header"></d>');
            $('#map_item_results_cont').append('<div class="stage">');
            if(resp.connection.connection_stage === "0"){
                $('.stage').append('<div class="fill_circle"></div>');
                $('.stage').append('<div class="empty_circle"></div>');
                $('.stage').append('<div class="empty_circle"></div>');
            }
            else if (resp.connection.connection_stage === "1"){
                $('.stage').append('<div class="fill_circle"></div>');
                $('.stage').append('<div class="fill_circle"></div>');
                $('.stage').append('<div class="empty_circle"></div>');
            }
            else{
                $('.stage').append('<div class="fill_circle"></div>');
                $('.stage').append('<div class="fill_circle"></div>');
                $('.stage').append('<div class="fill_circle"></div>');
            }

            $('#map_item_results_cont').append('<div class="container" id="map_items_boot">');
            $('#map_items_boot').append('<div class="row" id="map_item_person">');
            $('#map_item_person').append('<h4 id="map_from" class="col-xs-2">From:</h4>');
            $('#map_item_person').append('<div id="map_item_person_name" class="col-xs-6" style="padding-top: 7px;padding-left: 0px;">'+resp.connection.user_name+'</div>');
            $('#map_item_person').append('<h4 id="map_to" class="col-xs-1">To:</h4>');
            $('#map_item_person').append('<div id="map_item_person_to" class="col-xs-3" style="padding-top: 7px;padding-left: 5px;">'+resp.connection.personthing_name.substring(0,18)+'</div>');
            $('#map_item_results_cont').append('<div class="container" id="map_gift_boot">');
            $('#map_gift_boot').append('<div class="row" id="map_item_summary">');
            $('#map_item_summary').append('<h4 class="col-xs-2">Gift:</h4>');
            $('#map_item_summary').append('<div class="col-xs-10" style="padding-top: 7px;padding-left: 0px;">'+resp.connection.summary+'</div>');
            $('#map_item_results_cont').append('<div class="container" id="map_reas_boot">');
            $('#map_reas_boot').append('<div class="row" id="map_item_reason">');
            $('#map_item_reason').append('<h4 class="col-xs-2">Reason:</h4>');
            $('#map_item_reason').append('<div id="map_item_reason" class="col-xs-10" style="padding-top: 7px;padding-left: 0px;">'+resp.connection.req_reason+'</div>');
            $('#map_item_results_cont').append('<div class="container" id="map_share_boot">');
            $('#map_share_boot').append('<div class="row" id="map_item_share">');
            $('#map_item_share').append('<div class="col-xs-12" id="share_box"></div>');
            $('#share_box').append('<div class="col-xs-1" id="twitter_share_box"></div>');
            $('#twitter_share_box').append('<a href="http://twitter.com/intent/tweet?url='+resp.connection.social_media_json+'&text='+resp.connection.title+'&hashtags=alittlecloser&via=bealittlecloser" target="_blank"><img class="twitter_share" src="/img/twitter_wht.png"></a>');
            $('#share_box').append('<div class="col-xs-1" id="facebook_share_box"></div>');
            $('#facebook_share_box').append('<a href="https://www.facebook.com/sharer/sharer.php?u='+resp.connection.social_media_json+'" target="_blank"><img class="fb_share" src="/img/fb.png"></a>');

            $('#share_box').append('<div class="col-xs-1" id="close_box"></div>');
            $('#close_box').append('<a class="close_modal"><img class="fb_share" src="/img/close.png"></a>');


            $('#map_spinner').fadeOut();
            $('#map_item_results').fadeIn();

        });
    };

}




function connection_drawer(resp)
{
    $('#connection').append('<div class="container" id="connection_cont">');
    var n =0;
    for (var i=0,j=resp.connection.media.length;i<j;i++){
        if(resp.connection.media[i].filename === resp.connection.primary_media && n==0){
            if(resp.connection.media[i].media_item_message[0].file_cat==="image"){
                $('#connection_cont').append('<div class="row" id="big_row" ></div>');
                $('#big_row').append('<div class="col-md-12 col-xs-12 connect_holder"></div>');
                $('.connect_holder').append('<img class="col-md-12 col-xs-12"  data-filename="'+resp.connection.media[i].filename+'" src="'+resp.connection.media[i].media_item_message[3].blob_key+'=s1280" alt="Smiley face">');
                $('.connect_holder').append('<a><p class="item_title_conn">'+resp.connection.title+'</p></a>');
                $('.connect_holder').append('<div class="item_header_conn"></d>');
                $('.connect_holder').append('<div class="stage">');
                if(resp.connection.connection_stage === "0"){
                    $('.stage').append('<div class="fill_circle"></div>');
                    $('.stage').append('<div class="empty_circle"></div>');
                    $('.stage').append('<div class="empty_circle"></div>');
                }
                else if (resp.connection.connection_stage === "1"){
                    $('.stage').append('<div class="fill_circle"></div>');
                    $('.stage').append('<div class="fill_circle"></div>');
                    $('.stage').append('<div class="empty_circle"></div>');
                }
                else{
                    $('.stage').append('<div class="fill_circle"></div>');
                    $('.stage').append('<div class="fill_circle"></div>');
                    $('.stage').append('<div class="fill_circle"></div>');
                }

                $('#connection_cont').append('<div id="map_items_boot">');
                $('#map_items_boot').append('<div class="row" id="map_item_person">');
                $('#map_item_person').append('<h4 id="map_from" class="col-xs-2">From:</h4>');
                $('#map_item_person').append('<div id="map_item_person_name" class="col-xs-6" style="padding-top: 7px;padding-left: 0px;">'+resp.connection.user_name+'</div>');
                $('#map_item_person').append('<h4 id="map_to" class="col-xs-1">To:</h4>');
                $('#map_item_person').append('<div id="map_item_person_to" class="col-xs-3" style="padding-top: 7px;padding-left: 5px;">'+resp.connection.personthing_name+'</div>');
                $('#connection_cont').append('<div id="map_gift_boot">');
                $('#map_gift_boot').append('<div class="row" id="map_item_summary">');
                $('#map_item_summary').append('<h4 class="col-xs-2">Gift:</h4>');
                $('#map_item_summary').append('<div class="col-xs-10" style="padding-top: 7px;padding-left: 0px;">'+resp.connection.summary+'</div>');
                $('#connection_cont').append('<div id="map_reas_boot">');
                $('#map_reas_boot').append('<div class="row" id="map_item_reason">');
                $('#map_item_reason').append('<h4 class="col-xs-2">Reason:</h4>');
                $('#map_item_reason').append('<div id="map_item_reason" class="col-xs-10" style="padding-top: 7px;padding-left: 0px;">'+resp.connection.req_reason+'</div>');
                $('#connection_cont').append('<div id="map_share_boot">');
                $('#map_share_boot').append('<div class="row" id="map_item_share_par">');
                $('#map_item_share_par').append('<div class="col-xs-12 col-md-12" id="map_item_share">');
                $('#map_item_share').append('<div class="col-xs-12 col-md-12" id="share_box"></div>');
                $('#share_box').append('<div class="col-xs-1" id="twitter_share_box"></div>');
                $('#twitter_share_box').append('<a href="http://twitter.com/intent/tweet?url='+resp.connection.social_media_json+'&text='+resp.connection.title+'&hashtags=alittlecloser&via=bealittlecloser" target="_blank"><img class="twitter_share" src="/img/twitter_wht.png"></a>');
                $('#share_box').append('<div class="col-xs-1" id="facebook_share_box"></div>');
                $('#facebook_share_box').append('<a href="https://www.facebook.com/sharer/sharer.php?u='+resp.connection.social_media_json+'" target="_blank"><img class="fb_share" src="/img/fb.png"></a>');
                $('#share_box').append('<div class="col-xs-2 col-md-2" id="map_box"></div>');
                $('#map_box').append('<a href="'+resp.connection.social_media_json+'"><img class="map_link" src="/img/map.png">view on map</a>');
                $('#connection_cont').append('<div id="supporting">');
                $('#supporting').append('<div class="row" id="supporting_row">');
                $('#supporting_row').append('<h4 id="map_from" class="col-md-2 col-md-offset-5 col-xs-2 col-xs-offset-5" >Media & Comments</h4>');
            }
            n=1;
        }
        else{
            if(resp.connection.media[i].media_item_message[0].file_cat==="image"){
                $('#connection_cont').append('<div class="row support_image" data-filename="'+resp.connection.media[i].filename+'"><img class="col-md-12 col-xs-12" src="'+resp.connection.media[i].media_item_message[3].blob_key+'=s1280" alt="Smiley face"></div>');
            }
        }
    }
    $('#loading_div').hide();
    $('#connection').fadeIn();
}

function profile_drawer(resp)
{
    $('#connection').append('<div id="connection_cont">');
    $('#connection_cont').append('<img id="connection_item_primary" src="'+resp.connection.media[0].media_item_message[2].blob_key+'" alt="Smiley face">');
    $('#connection_cont').append('<div id="connection_item_header"></d>');
    $('#connection_cont').append('<p id="connection_item_type">'+resp.connection.type+'</p>');
    $('#connection_cont').append('<p id="connection_item_person">'+resp.connection.user_name+'</p>');
    $('#connection_cont').append('<a href="/closer/'+resp.connection.id+'"><p id="map_item_title">'+resp.connection.title+'</p></a>');
    $('#connection_cont').append('<p id="connection_item_stage">'+resp.connection.connection_stage+'</p>');
    $('#connection_cont').append('<p id="connection_item_summary">'+resp.connection.summary+'</p>');
    $('#connection_cont').append('<p id="connection_item_personthing">'+resp.connection.personthing_name+'</p>');
    $('#connection_cont').append('<img id="connection_item_tweet_url" src="'+resp.connection.id+'" alt="Smiley face" height="42" width="42">');
    $('#connection_cont').append('<img id="connection_item_fb_url" src="'+resp.connection.id+'" alt="Smiley face" height="42" width="42">');
    $('#connection_cont').append('<p id="connection_item_blog_url">'+resp.connection.id+'</p>');
    $('#connection_cont').append('<p id="connection_item_post_url">'+resp.connection.created+'</p>');

}



function addSearchTypeAhead(searchInput)
{

    $('#map_item_results').fadeOut(10);

    gapi.client.alittlecloser.search.query({'q':searchInput}).execute(function(resp){
        if (resp.message === "No results"){
            $('#map_search_results').empty();
            $('#map_search_results').append('<table id="map_search_results_search">');
            $('#map_search_results_search').append('<tr class="search_table_item"><td>No Results</td></tr>');
        }
        else{
            $('#map_search_results').empty();
            $('#map_search_results').append('<table id="map_search_results_search">');
            for(var i=0,m=resp.search.length;i<m;i++){
                {
                    var resultObj = resp.search[i];

                    $('#map_search_results_search').append('<tr class="search_table_item"><a><td data-id="'+resultObj.connection_id+'" data-lat="'+resultObj.latitude+'" data-lng="'+resultObj.longitude+'" class="search_result_list_item"><p class="search_result">'+resultObj.title+'</p><p class="search_person_name"></p></td></a></tr>');

                }}
        }
        $(".search_result_list_item").click(function() {
            alittlecloser.connection_map.setView([this.dataset.lat, this.dataset.lng], 13);
            alittlecloser.viewDetails(this.dataset.id);
        });
    });

}



//BLOG FUNCTIONS

$(document).on("click", ".tag_filter", function (e) {

    var blog_id = e.currentTarget.id;
    var offset = 0;
    var limit = 20;

    $("#current_tag").remove();
    $("#end_posts").empty();


    if (blog_id==="tag_filter_friptik"){
        var tag="&tag=Friptik";
        var continuos_scroll_tag = 'Friptik';
    }
    else if (blog_id==="tag_filter_design"){
        var tag="&tag=design";
        var continuos_scroll_tag = 'design';
    }
    else if (blog_id==="tag_filter_technology"){
        var tag="&tag=technology" ;
        var continuos_scroll_tag = 'technology';
    }
    else if (blog_id==="tag_filter_development"){
        var tag="&tag=development";
        var continuos_scroll_tag = 'development';
    }
    else if (blog_id==="tag_filter_data"){
        var tag="&tag=data";
        var continuos_scroll_tag = 'data';
    }
    else if (blog_id==="tag_filter_events"){
        var tag="&tag=events";
        var continuos_scroll_tag = 'events';
    }
    else  {
        var tag="";
    }

    $("#blog_holder").push('<div>Loading</div>');
    $.ajax({
        type: 'GET',
        url: '/blog_json', // or your absolute-path
        data: tag+'&offset='+offset+'&limit='+limit,
        dataType: 'json',
        complete: function (resp) {
            var json_object = jQuery.parseJSON(resp.responseText);
            $("#blog_holder").empty();
            parse_blog(json_object);
            $("#blog_holder").append('<div id="current_tag" hidden="true">'+continuos_scroll_tag+'</div>');
        }
    });
});



$(document).on("click", ".tag_in_blog", function (e) {
    var blog_id = e.currentTarget.innerHTML.substr(1);
    var tag="&tag=" + blog_id;
    $("#end_posts").empty();
    $("#current_tag").remove();

    $("#blog_holder").push('<div>Loading</div>');
    $.ajax({
        type: 'GET',
        url: '/blog_json', // or your absolute-path
        data: tag+'',
        dataType: 'json',
        complete: function (resp) {
            var json_object = jQuery.parseJSON(resp.responseText);
            $("#blog_holder").empty() ;
            parse_blog(json_object);
            $("#blog_holder").append('<div id="current_tag" hidden="true">'+blog_id+'</div>');
        }
    });
});


function parse_blog(json_object,offset){
    for (var i = 0; i < json_object.length; i++) {
        var tags = "";
        for (var j = 0; j < json_object[i].tags.length; j++) {
            if (! tags){
                tags = ('<div class="tags"><a class="tag_in_blog" href="#">#'+json_object[i].tags[j]+'</a></div>');
            }
            else{
                tags = tags + ('<div class="tags"><a class="tag_in_blog" href="#">#'+json_object[i].tags[j]+'</a></div>');
            }

        }

        console.log(json_object[i].date.substr(0,10).split('-')[1]);
        d = new XDate(json_object[i].date.substr(0,10).split('-')[0], json_object[i].date.substr(0,10).split('-')[1]-1, json_object[i].date.substr(0,10).split('-')[2]);
        var date_array = d.toString().split(' ');
        var date_share = '<div class="blog_date">'+ date_array[1] +' ' + date_array[2]+', ' +date_array[3]+' ' +'</div><div></div>';
        if (json_object[i].type === "text"){
            var blog_summary = json_object[i].body;

            if (! json_object[i].title)
                json_object[i].title = "Untitled";

            blog_summary = blog_summary.match(/<p>.+?<\/p>/);

            if (! blog_summary[0]){
                blog_summary = blog_summary;
            }
            else{
                blog_summary=blog_summary[0];
            }


            $("#blog_holder").append('<article class="blog_post" id="blog_' + json_object[i].id + '"><h3 class="blog_title">' + json_object[i].title + '</h3><div class="blog_footer">'+date_share+'</div><div id="blog_body_' + json_object[i].id + '" >' + json_object[i].body + '</div></article>');


        }
        if (json_object[i].type === "photo"){
            var photos;
            for (var j = 0; j < json_object[i].photos.length; j++) {
                if (! photos){
                    photos = ('<div class="photos"><img src="' + json_object[i].photos[j].alt_sizes[0].url +'"></div>');
                }
                else{
                    photos = photos + ('<div class="photos"><img src="' + json_object[i].photos[j].alt_sizes[0].url +'"></div>');
                }
            }

            $("#blog_holder").append('<article class="blog_post" id="blog_' + json_object[i].id + '"><div id="blog_body_' + json_object[i].id + '" >'+photos+'</div><div class="image_caption">' + json_object[i].caption + '</div><div class="blog_footer">'+tags+date_share+'</div></article>');
        }
        if (json_object[i].type === "quote"){
            $("#blog_holder").append('<article class="blog_post" id="blog_' + json_object[i].id + '"><h3>' + json_object[i].text + '</h3></div></article>');
        }
        if (json_object[i].type === "link"){
            $("#blog_holder").append('<article class="blog_post" id="blog_' + json_object[i].id + '"><h3>' + json_object[i].title + '</h3><div id="blog_body_' + json_object[i].id + '" >' + json_object[i].description +'"</div></article>');
        }
        if (json_object[i].type === "audio"){
            $("#blog_holder").append('<article class="blog_post" id="blog_' + json_object[i].id + '"><h3>' + json_object[i].caption + '</h3><div id="blog_body_' + json_object[i].id + '" >' + json_object[i].player +'"</div></article>');
        }
        if (json_object[i].type === "video"){

            $("#blog_holder").append('<article class="blog_post" id="blog_' + json_object[i].id + '"><div class="videoWrapper" id="blog_body_' + json_object[i].id + '" ><iframe  src="//player.vimeo.com/video/'+json_object[i].permalink_url.split("/")[json_object[i].permalink_url.split("/").length-1]+'" width="560" height="349" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe></div><div>' + json_object[i].caption + '</div></article>');
        }
        if (json_object[i].type === "chat"){
            $("#blog_holder").append('<article class="blog_post" id="blog_' + json_object[i].id + '"><h3>Chat</h3><div id="blog_body_' + json_object[i].id + '" >' + json_object[i].body +'</div></article>');
        }
        $("#blog_holder").append('<hr>');

    }
    var new_offset = json_object.length;
    if (offset){
        new_offset = parseInt(new_offset)+parseInt(offset);
    }
    $("#blog_holder").append('<div id="next_results" hidden="true">'+new_offset+'</div>');
}

$(document).ready(function () {
    $("#blog_close").click(function () {
        $("#blog_holder").empty();
    });
});
$(document).on("click", ".read_more", function (e) {
    var blog_id = e.currentTarget.id.substr(10);
    $('#blog_body_' + blog_id).show('slow');
    $('#blog_summary_' + blog_id).hide('');
    $('#blog_read_' + blog_id).hide('');
});

function throttle(func, wait) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        if (!timeout) {
            // the first time the event fires, we setup a timer, which
            // is used as a guard to block subsequent calls; once the
            // timer's handler fires, we reset it and create a new one
            timeout = setTimeout(function() {
                timeout = null;
                func.apply(context, args);
            }, wait);
        }
    };
}