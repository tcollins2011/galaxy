define("mvc/workflow/workflow-canvas",["exports"],function(t){"use strict";function e(t,e,i){this.app=t,this.cv=e,this.cc=this.cv.find("#canvas-container"),this.overview=i,this.oc=i.find("#overview-canvas"),this.ov=i.find("#overview-viewport"),this.init_drag(),this.init_copy_paste()}function i(t){this.panel=t}Object.defineProperty(t,"__esModule",{value:!0}),$.extend(e.prototype,{init_drag:function(){var t=this,e=function(e,i){e=Math.min(e,t.cv.width()/2),e=Math.max(e,-t.cc.width()+t.cv.width()/2),i=Math.min(i,t.cv.height()/2),i=Math.max(i,-t.cc.height()+t.cv.height()/2),t.cc.css({left:e,top:i}),t.cv.css({"background-position-x":e,"background-position-y":i}),t.update_viewport_overlay()};this.cc.each(function(){this.scroll_panel=new i(this)});var o,n;this.cv.bind("click",function(){document.activeElement.blur()}).bind("dragstart",function(){var e=$(this).offset(),i=t.cc.position();n=i.top-e.top,o=i.left-e.left}).bind("drag",function(t,i){e(i.offsetX+o,i.offsetY+n)}).bind("dragend",function(){t.app.workflow.fit_canvas_to_nodes(),t.draw_overview()}),this.overview.click(function(i){if(t.overview.hasClass("blockaclick"))t.overview.removeClass("blockaclick");else{var o=t.cc.width(),n=t.cc.height(),a=t.oc.width(),c=t.oc.height(),s=i.pageX-t.oc.offset().left-t.ov.width()/2,h=i.pageY-t.oc.offset().top-t.ov.height()/2;e(-s/a*o,-h/c*n),t.app.workflow.fit_canvas_to_nodes(),t.draw_overview()}}),this.ov.bind("drag",function(i,o){var n=t.cc.width(),a=t.cc.height(),c=t.oc.width(),s=t.oc.height(),h=o.offsetX-t.overview.offset().left,r=o.offsetY-t.overview.offset().top;e(-h/c*n,-r/s*a)}).bind("dragend",function(){t.overview.addClass("blockaclick"),t.app.workflow.fit_canvas_to_nodes(),t.draw_overview()}),$("#overview-border").bind("drag",function(e,i){var o=$(this).offsetParent(),n=o.offset(),a=Math.max(o.width()-(i.offsetX-n.left),o.height()-(i.offsetY-n.top));$(this).css({width:a,height:a}),t.draw_overview()}),$("#overview-border div").bind("drag",function(){})},init_copy_paste:function(){var t=this;document.addEventListener("copy",function(e){""===window.getSelection().toString()&&(t.app.workflow.active_node&&e.clipboardData.setData("application/json",JSON.stringify({nodeId:t.app.workflow.active_node.id})),e.preventDefault())}),document.addEventListener("paste",function(e){if(document.activeElement&&"textarea"!==document.activeElement.type&&"text"!==document.activeElement.type){var i;try{i=JSON.parse(e.clipboardData.getData("application/json")).nodeId}catch(t){}i&&t.app.workflow.nodes.hasOwnProperty(i)&&t.app.workflow.nodes[i].clone(),e.preventDefault()}})},update_viewport_overlay:function(){var t=this.cc,e=this.cv,i=this.oc,o=this.ov,n=t.width(),a=t.height(),c=i.width(),s=i.height(),h=t.position();o.css({left:-h.left/n*c,top:-h.top/a*s,width:e.width()/n*c-2,height:e.height()/a*s-2})},draw_overview:function(){var t,e,i,o,n=$("#overview-canvas"),a=n.parent().parent().width(),c=n.get(0).getContext("2d"),s=$("#canvas-container").width(),h=$("#canvas-container").height(),r=this.cv.width(),f=this.cv.height();s<r&&h<f?(o=(a-(i=s/r*a))/2,e=(a-(t=h/f*a))/2):s<h?(e=0,t=a,o=(a-(i=Math.ceil(t*s/h)))/2):(i=a,o=0,e=(a-(t=Math.ceil(i*h/s)))/2),n.parent().css({left:o,top:e,width:i,height:t}),n.attr("width",i),n.attr("height",t),$.each(this.app.workflow.nodes,function(e,o){c.fillStyle="#D2C099",c.strokeStyle="#D8B365",c.lineWidth=1;var n=$(o.element),a=n.position(),r=a.left/s*i,f=a.top/h*t,d=n.width()/s*i,v=n.height()/h*t;o.errors?(c.fillStyle="#FFCCCC",c.strokeStyle="#AA6666"):void 0!==o.workflow_outputs&&o.workflow_outputs.length>0&&(c.fillStyle="#E8A92D",c.strokeStyle="#E8A92D"),c.fillRect(r,f,d,v),c.strokeRect(r,f,d,v)}),this.update_viewport_overlay()}}),$.extend(i.prototype,{test:function(t,e){var i=this;clearTimeout(this.timeout);var o=t.pageX,n=t.pageY,a=$(this.panel),c=a.position(),s=a.width(),h=a.height(),r=a.parent(),f=r.width(),d=r.height(),v=r.offset(),p=v.left,l=v.top,w=p+r.width(),u=l+r.height(),g=-(s-f/2),_=-(h-d/2),m=f/2,k=d/2,y=!1,b=0;o-5<p?c.left<m&&(b=Math.min(23,m-c.left),a.css("left",c.left+b),y=!0):o+5>w?c.left>g&&(b=Math.min(23,c.left-g),a.css("left",c.left-b),y=!0):n-5<l?c.top<k&&(b=Math.min(23,k-c.top),a.css("top",c.top+b),y=!0):n+5>u&&c.top>_&&(b=Math.min(23,c.top-g),a.css("top",c.top-b+"px"),y=!0),y&&(e(),this.timeout=setTimeout(function(){i.test(t,e)},50))},stop:function(){clearTimeout(this.timeout)}}),t.default=e});