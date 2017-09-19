"use strict";define(["layout/masthead","utils/utils","libs/toastr","mvc/library/library-model","mvc/library/library-folderrow-view","mvc/library/library-dataset-view"],function(e,t,i,o,s,r){return{FolderListView:Backbone.View.extend({el:"#folder_items_element",progress:0,progressStep:1,folderContainer:null,sort:"asc",events:{"click #select-all-checkboxes":"selectAll","click .dataset_row":"selectClickedRow","click .folder_row":"selectClickedRow","click .sort-folder-link":"sortColumnClicked"},collection:null,defaults:{include_deleted:!1,page_count:null,show_page:null},initialize:function(e){this.options=_.defaults(this.options||{},this.defaults,e),this.modal=null,this.rowViews={},this.collection=new o.Folder,this.listenTo(this.collection,"add",this.renderOne),this.listenTo(this.collection,"remove",this.removeOne),this.listenTo(this.collection,"sort",this.rePaint),this.listenTo(this.collection,"reset",this.rePaint),this.fetchFolder()},fetchFolder:function(e){var e=e||{};this.options.include_deleted=e.include_deleted;var t=this;this.folderContainer=new o.FolderContainer({id:this.options.id}),this.folderContainer.url=this.folderContainer.attributes.urlRoot+this.options.id+"/contents",this.options.include_deleted&&(this.folderContainer.url=this.folderContainer.url+"?include_deleted=true"),this.folderContainer.fetch({success:function(e){t.folder_container=e,t.render()},error:function(e,t){void 0!==t.responseJSON?i.error(t.responseJSON.err_msg+" Click this to go back.","",{onclick:function(){Galaxy.libraries.library_router.back()}}):i.error("An error occurred. Click this to go back.","",{onclick:function(){Galaxy.libraries.library_router.back()}})}})},render:function(e){this.options=_.extend(this.options,e);var t=this.templateFolder();$(".tooltip").hide();var o,s=this.folderContainer.attributes.metadata.full_path;if(o=1===s.length?0:s[s.length-2][0],this.$el.html(t({path:this.folderContainer.attributes.metadata.full_path,parent_library_id:this.folderContainer.attributes.metadata.parent_library_id,id:this.options.id,upper_folder_id:o,order:this.sort})),this.options.dataset_id){var r=_.findWhere(that.rowViews,{id:this.options.dataset_id});r?r.showDatasetDetails():i.error("Requested dataset not found. Showing folder instead.")}else(null===this.options.show_page||this.options.show_page<1)&&(this.options.show_page=1),this.paginate();$("#center [data-toggle]").tooltip(),$("#center").css("overflow","auto")},paginate:function(e){this.options=_.extend(this.options,e),(null===this.options.show_page||this.options.show_page<1)&&(this.options.show_page=1),this.options.total_items_count=this.folder_container.get("folder").models.length,this.options.page_count=Math.ceil(this.options.total_items_count/Galaxy.libraries.preferences.get("folder_page_size"));var t=Galaxy.libraries.preferences.get("folder_page_size")*(this.options.show_page-1),i=null;i=this.folder_container.get("folder").models.slice(t,t+Galaxy.libraries.preferences.get("folder_page_size")),this.options.items_shown=i.length,Galaxy.libraries.preferences.get("folder_page_size")*this.options.show_page>this.options.total_items_count+Galaxy.libraries.preferences.get("folder_page_size")&&(i=[]),Galaxy.libraries.folderToolbarView.renderPaginator(this.options),this.collection.reset(i)},rePaint:function(e){this.options=_.extend(this.options,e),this.removeAllRows(),this.renderAll(),this.checkEmptiness()},addAll:function(e){_.each(e,function(e){Galaxy.libraries.folderListView.collection.add(e,{sort:!1})}),$("#center [data-toggle]").tooltip(),this.checkEmptiness(),this.postRender()},postRender:function(){var e=this.folderContainer.attributes.metadata;e.contains_file_or_folder=void 0!==this.collection.findWhere({type:"file"})||void 0!==this.collection.findWhere({type:"folder"}),Galaxy.libraries.folderToolbarView.configureElements(e)},renderAll:function(){var e=this;_.each(this.collection.models.reverse(),function(t){e.renderOne(t)}),this.postRender()},renderOne:function(e){this.options.contains_file_or_folder=!0,e.set("folder_id",this.id);var t=new s.FolderRowView({model:e});this.rowViews[e.get("id")]=t,this.$el.find("#first_folder_item").after(t.el)},removeOne:function(e){this.$el.find("tr").filter(function(){return $(this).data("id")&&$(this).data("id")===e.id}).remove()},removeAllRows:function(){$(".library-row").remove()},checkEmptiness:function(){0===this.$el.find(".dataset_row").length&&0===this.$el.find(".folder_row").length?this.$el.find(".empty-folder-message").show():this.$el.find(".empty-folder-message").hide()},sortColumnClicked:function(e){e.preventDefault(),"asc"===this.sort?(this.sortFolder("name","desc"),this.sort="desc"):(this.sortFolder("name","asc"),this.sort="asc"),this.renderSortIcon()},sortFolder:function(e,t){if("undefined"===e&&"undefined"===t)return this.collection.sortByNameAsc();if("name"===e){if("asc"===t)return this.collection.sortByNameAsc();if("desc"===t)return this.collection.sortByNameDesc()}},selectAll:function(e){var t=e.target.checked;that=this,$(":checkbox","#folder_list_body").each(function(){this.checked=t;var e=$(this).closest("tr");t?that.makeDarkRow(e):that.makeWhiteRow(e)})},selectClickedRow:function(e){var t,i,o="";t=$(e.target).closest("tr"),"input"===e.target.localName?(o=e.target,i="input"):"td"===e.target.localName&&(o=t.find(":checkbox")[0],i="td"),o.checked?"td"===i?(o.checked="",this.makeWhiteRow(t)):"input"===i&&this.makeDarkRow(t):"td"===i?(o.checked="selected",this.makeDarkRow(t)):"input"===i&&this.makeWhiteRow(t)},makeDarkRow:function(e){e.removeClass("light").addClass("dark"),e.find("a").removeClass("light").addClass("dark"),e.find(".fa-file-o").removeClass("fa-file-o").addClass("fa-file"),e.find(".fa-folder-o").removeClass("fa-folder-o").addClass("fa-folder")},makeWhiteRow:function(e){e.removeClass("dark").addClass("light"),e.find("a").removeClass("dark").addClass("light"),e.find(".fa-file").removeClass("fa-file").addClass("fa-file-o"),e.find(".fa-folder").removeClass("fa-folder").addClass("fa-folder-o")},renderSortIcon:function(){"asc"===this.sort?$(".sort-icon").removeClass("fa-sort-alpha-desc").addClass("fa-sort-alpha-asc"):$(".sort-icon").removeClass("fa-sort-alpha-asc").addClass("fa-sort-alpha-desc")},templateFolder:function(){return _.template(['<ol class="breadcrumb">','<li><a title="Return to the list of libraries" href="#">Libraries</a></li>',"<% _.each(path, function(path_item) { %>","<% if (path_item[0] != id) { %>",'<li><a title="Return to this folder" href="#/folders/<%- path_item[0] %>"><%- path_item[1] %></a> </li> ',"<% } else { %>",'<li class="active"><span title="You are in this folder"><%- path_item[1] %></span></li>',"<% } %>","<% }); %>","</ol>",'<table data-library-id="<%- parent_library_id  %>" id="folder_table" class="grid table table-condensed">',"<thead>",'<th class="button_heading"></th>','<th style="text-align: center; width: 20px; " title="Check to select all datasets"><input id="select-all-checkboxes" style="margin: 0;" type="checkbox"></th>','<th><a class="sort-folder-link" title="Click to reverse order" href="#">name</a> <span title="Sorted alphabetically" class="sort-icon fa fa-sort-alpha-<%- order %>"></span></th>','<th style="width:25%;">description</th>','<th style="width:5%;">data type</th>','<th style="width:10%;">size</th>','<th style="width:160px;">time updated (UTC)</th>','<th style="width:10%;"></th> ',"</thead>",'<tbody id="folder_list_body">','<tr id="first_folder_item">',"<td>",'<a href="#<% if (upper_folder_id !== 0){ print("folders/" + upper_folder_id)} %>" title="Go to parent folder" class="btn_open_folder btn btn-default btn-xs">..<a>',"</td>","<td></td>","<td></td>","<td></td>","<td></td>","<td></td>","<td></td>","<td></td>","</tr>","</tbody>","</table>",'<div class="empty-folder-message" style="display:none;">',"This folder is either empty or you do not have proper access permissions to see the contents. If you expected something to show up",' please consult the <a href="https://galaxyproject.org/data-libraries/#permissions" target="_blank">library security wikipage</a>',' or visit the <a href="https://biostar.usegalaxy.org/" target="_blank">Galaxy support site</a>.',"</div>"].join(""))}})}});
//# sourceMappingURL=../../../maps/mvc/library/library-folderlist-view.js.map
