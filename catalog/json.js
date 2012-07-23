                $(function(){
                        $(document).bind("contextmenu",function(e){
                          return false;
                        }); 
                       $('#jsoninput').hide(); 
                        $('#json_editor').html('');
                        json_editor('json_editor',$('#jsoninput').val());
			//META
                       $('#jsoninput_meta').hide();
                        $('#json_editor_meta').html('');
                       // json_editor('json_editor_meta',$('#jsoninput_meta').val());
                      $('#jsoninput_location').hide();
			$('#json_editor_loc').html('');
			//json_editor('json_editor_loc',$('#jsoninput_location').val());
                        // add the jquery editing magic
                        apply_editlets();

                       // $('#jsoninput').click(function(){
                       //         $(this).focus();
                       //         $(this).select();
                       // });
                });
                
                // stuff for the modal ws window
                function display_ws_modal() {
                        var id = '#dialog';
                        //transition effect     
                        $('#mask').fadeIn(500);    
                        $('#mask').fadeTo("slow",0.8);  
                        
                        //Get the window height and width
                        var winH = $(window).height();
                        var winW = $(window).width();
                               
                        //Set the popup window to center
                        $(id).css('top',  winH/2-$(id).height()/2);
                        $(id).css('left', winW/2-$(id).width()/2);
                        
                        //transition effect
                        $(id).fadeIn(1000); 
                }

                // stuff for the right click menus
                function setup_menu() {
                        $('div[data-role="arrayitem"]').contextMenu('context-menu1', {
                            'remove item': {
                                click: remove_item,
                                klass: "menu-item-1" // a custom css class for this menu item (usable for styling)
                            },
                        }, menu_options);
                        $('div[data-role="prop"]').contextMenu('context-menu2', {
                            'remove item': {
                                click: remove_item,
                                klass: "menu-item-1" // a custom css class for this menu item (usable for styling)
                            },
                        }, menu_options);
                }
                function remove_item(element) {
                      //console.log("# delete");
                      element.hide(500, function () {
                              $(this).remove();
                      });
                }
                function create_item(element) {
                      //console.log("# create");
                }
                var menu_options = {
                        disable_native_context_menu: false,//true,
                        showMenu: function(element) {
                                element.addClass('dimmed');
                        },
                        hideMenu: function(element) {
                                element.removeClass('dimmed');
                        },
                };
                var easy_save_value = function(value, settings) { 
                        $(this).text(value);
                }
                var save_value = function(value, settings) { 
                        //console.log(this); console.log(value); // console.log(settings);

                        if ($(this).data('role') == 'value') {
                                if (value == "null") {
                                        $(this).attr("data-type", "null");
                                        $(this).data('type','null');
                                        $(this).text(value);
                                        $(this).unbind('click');
                                } else if (value == "true" || value == "false") {
                                        $(this).attr("data-type", "boolean");
                                        $(this).data('type','boolean');
                                        $(this).text(value);
                                        $(this).unbind();
                                        $(this).editable(save_value,{ cssclass : 'edit_box', height:'20px', width:'100px', data : "{'true':'true','false':'false'}", type : 'select', onblur : 'submit' });
                                } else {
                                        var num = parseFloat(value);
                                        //console.log(num);
                                        if (isNaN(num)) {
                                                $(this).attr("data-type", "string");
                                                $(this).data('type','string');
                                                $(this).text(value);
                                                $(this).unbind();
                                                $(this).editable(save_value, { cssclass : 'edit_box', height:'20px', width:'50px'});
                                        } else {
                                                $(this).attr("data-type", "number");
                                                $(this).data('type','number');
                                                $(this).text(num);
                                                $(this).unbind();
                                                $(this).editable(save_value, { cssclass : 'edit_box', height:'20px', width:'150px'});
                                        }
                                }
                        } else {
                                $(this).text(value);
                        }
                };
                // copy the workspace back into the textarea
                function extract_json(divid, indent){
                        $('#jsoninput').val(glean_json(divid,indent));
                }
                // convert the work area to a json string
                function glean_json(divid, indent)  {
                        var base = $('#' + divid);
                        var rootnode = base.children('div[data-role="value"]:first');
                        var jsObject = parse_node(rootnode);
                        var json = JSON.stringify(jsObject, null, indent);
                        return json;
                }
		function getRecordsNeedSave() {
			var oldObj = JSON.parse($('#jsoninput').val());
			///glean_json('json_editor')
			var base = $('#json_editor');
			var rootnode = base.children('div[data-role="value"]:first');
                        var jsObject = parse_node(rootnode);
			return JSON.stringify(getDifferences(oldObj, jsObject),null,0);
		}
		function getDifferences(oldObj, newObj) {
   			 var diff ={'new':[],'update': [],'delete':[]};
			var newRec = true;
   		     	for (var k in oldObj) {
				var found='N'
				for (var n in newObj){
				 if('_id' in newObj[n]){
				 	if(oldObj[k]._id === newObj[n]._id){//.$oid
						found='Y'
						if (JSON.stringify(oldObj[k]) !== JSON.stringify(newObj[n])){
							diff['update'].push(newObj[n]);
						}}
					
				}else{ if(newRec){diff['new'].push(newObj[n]);}}}
				newRec=false;
				if(found ==='N'){diff['delete'].push(oldObj[k])}
			}
      				//if (!(k in newObj))
         			//	diff[k] = undefined;  // property gone so explicitly set it undefined
      				//else if (JSON.stringify(oldObj[k]) !== JSON.stringify(newObj[k]))
         			//	diff[k] = newObj[k];  // property in both but has changed
  				// }	

   			//for (k in newObj) {
      			//	if (!(k in oldObj))
         		//		diff[k] = newObj[k]; // property is new
   			//}

   			return diff;
		}
                // convert the work area to a js object
                function parse_node(node) {
                        var type = node.data('type');
                        if (type == 'object') {
                                var newNode = new Object();
                                var props = node.children('div[data-role="prop"]');
                                props.each(function(index) {
                                        newNode[$(this).children('[data-role="key"]').html()] = parse_node($(this).children('[data-role="value"]'));
                                });
                                return newNode;
                        } else if (type == 'array') {
                                var newNode = new Array();
                                var values = node.children('[data-role="arrayitem"]');
                                values.each(function(index) {
                                        var value_node = $(this).children('[data-role="value"]');
                                        newNode.push(parse_node(value_node));
                                });
                                return newNode;
                        } else if (type == 'string') {
                                return node.html();
                        } else if (type == 'number') {
                                var parsedNum = parseFloat(node.html());
                                if(isNaN(parsedNum)) return 0;
                                return parsedNum;
                        } else if (type == 'boolean') {
                                return (node.html() == "true") ;
                        } else if (type == null || type == 'null' ) {
                                return null;
                        } else {
                                return "(Unknown Type:" + type + " )";
                        }
                }
                function remove_editlets() {
                        $("span.collapse_box").remove();
                        $("div.inline_add_box").remove();
                        $(".context-menu").remove();

                }
                function apply_editlets() {
                        remove_editlets();
                        // add collapse boxes for the arrays and objects
                        var o_collapse_box = $('<span class="collapse_box"><span>[-]</span><span style="display: none">[+] {...}</span></span>');
                        var a_collapse_box = $('<span class="collapse_box"><span>[-]</span><span style="display: none" data-role="counter">[+] []</span></span>');
                        $('div[data-type="object"]').before(o_collapse_box );
                        $('div[data-type="array"]').before(a_collapse_box );

                        $('.collapse_box').click(function(){
                                var next = $(this).next();
                                next.toggle();
                                $(this).find('span').toggle();
                                if ( next.data('type') == 'array' ) {
                                        $(this).find('span[data-role="counter"]').html('[+] ['+ next.children('[data-role="arrayitem"]').length +']' );
                                }
                                event.stopPropagation();
                        });
                        // add the "new" buttons
                        var add_more_box = $('<div class="inline_add_box"><div class="add_box_content">add: <a data-task="add_value" href="#">text</a> | <a data-task="add_array" href="#">array</a> | <a data-task="add_object" href="#">object</a></div></div>');
                        $('div[data-type="object"]').append(add_more_box);
                        $('div[data-type="array"]').append(add_more_box);
                        
                        $('div.inline_add_box a').click(function(e){
                                var target = $(e.target);
                                var task = target.data('task');
                                var add_box = target.parents(".inline_add_box");
                                var collection = add_box.parent();                              
                                var type = collection.data('type');

                                // TODO this code is a partial duplicate of code in make_node fix it!
                                if (type == 'object') {
                                        var newObj = $('<div data-role="prop"></div>').append( $('<span data-role="key">').append("key")).append(': ');
                                } else {
                                        var newObj = $('<div data-role="arrayitem"></div>');
                                }
                                
                                if (task == 'add_object') {
                                        var json = '{"id":"1"}';
                                        newObj.append(make_node(JSON.parse(json)));
                                } else if (task == 'add_array') {
                                        var json = '["item1"]';
                                        newObj.append(make_node(JSON.parse(json)));
                                } else {
                                        newObj.append($('<pre data-role="value" data-type="string">').html("value"));
                                }
                                newObj.hide();
                                add_box.before(newObj);
                                newObj.show(500);
                                apply_editlets();
                                return false;
                        });
                        
                        $(".inline_add_box").hover(
                                function () {
                                        $(this).children().show(100);
                                },
                                function () {
                                        $(this).children().hide(200);
                                }
                        );

                        // make the fields editable in place
                        $('span[data-role="key"]').editable(easy_save_value,{ cssclass : 'edit_box', height:'20px'});
                        $('[data-type="string"]').editable(save_value, { cssclass : 'edit_box', height:'20px'});
                        $('[data-type="number"]').editable(save_value, { cssclass : 'edit_box', height:'20px'});
                        $('[data-type="null"]').editable(save_value, { cssclass : 'edit_box', height:'20px', width:'150px'});
                        $('[data-type="boolean"]').editable(save_value,{ cssclass : 'edit_box', height:'20px', width:'100px', data : "{'true':'true','false':'false'}", type : 'select', onblur : 'submit' });
                        
                        // make the right click menus
                        setup_menu();

                }
                // parse the text area into the the workarea, setup the event handlers
                function load_from_box() {
                        $('#json_editor').html('');
                        json_editor('json_editor', $('#jsoninput').val());

                        // add the jquery editing magic
                        apply_editlets();
                }
                function load_from_url(url) {
                    $('#json_editor').html('loading......');
                    items1 =[];
                    var url1="http://fire.rccc.ou.edu/mongo/db_find/flora/data/{'fields':{'REF_NO':1,'Sitename':1,'State':1,'Year':1,'midlat':1,'midlon':1,'NO_Species':1,'Area_hectares':1}}?callback=?";
                        $.getJSON(url, function(fdata){
                                //alert(fdata.items);
                                //$.each(fdata.items, function(key, val) {
                                //items1.push(val);});
                        //alert(items);
                        try {
                        $('#json_editor').html('');
                        var base = $('#json_editor');
                        base.append(make_node(fdata));
                        } catch (err) {
                        var json = JSON.parse('{"error": "parse failed"}');
                        }
                        //json_editor('json_editor',JSON.stringify(fdata.items));
                        //$('#jsoninput').val(fdata.items);
                        apply_editlets();
                        });
                        // add the jquery editing magic
                        //apply_editlets();
                }
                // convert a string into nodes
                function json_editor(divid, json_string){
                        try {
                        var json = JSON.parse(json_string);
                        } catch (err) {
                        var json = JSON.parse('{"error": "parse failed"}');
                        }
                        var base = $('#' + divid);
                        base.append(make_node(json));
                }
                // recursively make html nodes out of the json
                function make_node(node_in) {
                        //console.log(" ====> " + JSON.stringify(node_in));
                        var type = Object.prototype.toString.apply(node_in);
                        //console.log("  - " + type);

                        if (type === "[object Object]") {
                                // TODO create the div for an object here
                                var container = $('<div data-role="value" data-type="object"></div>');
                                for(var prop in node_in) {
                                        if(node_in.hasOwnProperty(prop)) {
                                                var row = $('<div data-role="prop"></div>').append( $('<span data-role="key">').append(prop)).append(': ').append(make_node(node_in[prop]));
                                                container.append(row);
                                        }
                                }
                                return container;
                        } else if (type === "[object Array]") {
                                var container = $('<div data-role="value" data-type="array"></div>');
                                for (var i = 0, j = node_in.length; i < j; i++) {
                                        var row = $('<div data-role="arrayitem"></div>').append(make_node(node_in[i]));
                                        container.append(row);
                                }
                                return container;
                        } else if (type === "[object String]") {
                                return $('<pre data-role="value" data-type="string">').html(node_in);
                        } else if (type === "[object Number]") {
                                return $('<pre data-role="value" data-type="number">').html(node_in);
                        } else if (type === "[object global]" || type === "[object Null]") {
                                return $('<pre data-role="value" data-type="null">').html('null');
                        } else if (type === "[object Boolean]") {
                                return $('<pre data-role="value" data-type="boolean">').html(node_in.toString());
                        }
                }

