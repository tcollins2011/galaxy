"use strict";define(["mvc/workflow/workflow-globals","mvc/workflow/workflow-terminals","mvc/workflow/workflow-connector"],function(e,n,t){var i=Backbone.View.extend({tagName:"div",className:"fa-icon-button fa fa-folder-o",initialize:function(e){this.$el.tooltip({delay:500,title:"Run tool in parallel over collection"}),this.model.bind("change",_.bind(this.render,this))},render:function(){this.model.mapOver.isCollection?this.$el.show():this.$el.hide()}}),a=i.extend({events:{click:"onClick",mouseenter:"onMouseEnter",mouseleave:"onMouseLeave"},onMouseEnter:function(e){var n=this.model;!n.terminal.connected()&&n.mapOver.isCollection&&this.$el.css("color","red")},onMouseLeave:function(e){this.$el.css("color","black")},onClick:function(e){var n=this.model;!n.terminal.connected()&&n.mapOver.isCollection&&n.terminal.resetMapping()}}),o=Backbone.View.extend({setupMappingView:function(e){var n=new this.terminalMappingClass({terminal:e}),t=new this.terminalMappingViewClass({model:n});t.render(),e.terminalMappingView=t,this.terminalMappingView=t},terminalElements:function(){return this.terminalMappingView?[this.terminalMappingView.el,this.el]:[this.el]}}),r=o.extend({className:"terminal input-terminal",initialize:function(e){var n=e.node,t=e.input,i=t.name,a=this.terminalForInput(t);a.multiple||this.setupMappingView(a),this.el.terminal=a,a.node=n,a.name=i,n.input_terminals[i]=a},events:{dropinit:"onDropInit",dropstart:"onDropStart",dropend:"onDropEnd",drop:"onDrop",hover:"onHover"},onDropInit:function(e,n){var t=this.el.terminal;return $(n.drag).hasClass("output-terminal")&&t.canAccept(n.drag.terminal)},onDropStart:function(e,n){n.proxy.terminal&&(n.proxy.terminal.connectors[0].inner_color="#BBFFBB")},onDropEnd:function(e,n){n.proxy.terminal&&(n.proxy.terminal.connectors[0].inner_color="#FFFFFF")},onDrop:function(e,n){var i=this.el.terminal;new t(n.drag.terminal,i).redraw()},onHover:function(){var e=this.el,n=e.terminal;if(n.connectors.length>0){var t=$("<div class='callout'></div>").css({display:"none"}).appendTo("body").append($("<div class='button'></div>").append($("<div/>").addClass("fa-icon-button fa fa-times").click(function(){$.each(n.connectors,function(e,n){n&&n.destroy()}),t.remove()}))).bind("mouseleave",function(){$(this).remove()});t.css({top:$(e).offset().top-2,left:$(e).offset().left-t.width(),"padding-right":$(e).width()}).show()}}}),l=r.extend({terminalMappingClass:n.TerminalMapping,terminalMappingViewClass:a,terminalForInput:function(e){return new n.InputTerminal({element:this.el,input:e})}}),s=r.extend({terminalMappingClass:n.TerminalMapping,terminalMappingViewClass:a,terminalForInput:function(e){return new n.InputCollectionTerminal({element:this.el,input:e})}}),p=o.extend({className:"terminal output-terminal",initialize:function(e){var n=e.node,t=e.output,i=t.name,a=this.terminalForOutput(t);this.setupMappingView(a),this.el.terminal=a,a.node=n,a.name=i,n.output_terminals[i]=a},events:{drag:"onDrag",dragstart:"onDragStart",dragend:"onDragEnd"},onDrag:function(n,t){var i=function(){var n=$(t.proxy).offsetParent().offset(),i=t.offsetX-n.left,a=t.offsetY-n.top;$(t.proxy).css({left:i,top:a}),t.proxy.terminal.redraw(),e.canvas_manager.update_viewport_overlay()};i(),$("#canvas-container").get(0).scroll_panel.test(n,i)},onDragStart:function(i,a){$(a.available).addClass("input-terminal-active"),e.workflow.check_changes_in_active_form();var o=$('<div class="drag-terminal" style="position: absolute;"></div>').appendTo("#canvas-container").get(0);o.terminal=new n.OutputTerminal({element:o});var r=new t;return r.dragging=!0,r.connect(this.el.terminal,o.terminal),o},onDragEnd:function(e,n){var t=n.proxy.terminal.connectors[0];t&&t.destroy(),$(n.proxy).remove(),$(n.available).removeClass("input-terminal-active"),$("#canvas-container").get(0).scroll_panel.stop()}});return{InputTerminalView:l,OutputTerminalView:p.extend({terminalMappingClass:n.TerminalMapping,terminalMappingViewClass:i,terminalForOutput:function(e){var t=e.extensions;return new n.OutputTerminal({element:this.el,datatypes:t})}}),InputCollectionTerminalView:s,OutputCollectionTerminalView:p.extend({terminalMappingClass:n.TerminalMapping,terminalMappingViewClass:i,terminalForOutput:function(e){var t=e.collection_type,i=e.collection_type_source;return new n.OutputCollectionTerminal({element:this.el,collection_type:t,collection_type_source:i,datatypes:e.extensions})}})}});
//# sourceMappingURL=../../../maps/mvc/workflow/workflow-view-terminals.js.map
