"use strict";define(["mvc/ui/popup-menu","mvc/history/copy-dialog","mvc/base-mvc","utils/localization","mvc/webhooks"],function(e,t,r,a,o){function n(e,t,r){return _.clone(l).filter(function(a){return!(e&&!a.anon)&&(!(!t&&a.purge)&&(a.href&&(a.href=r+a.href,a.target=a.target||"galaxy_main"),a.confirm&&(a.func=function(){confirm(a.confirm)&&(galaxy_main.location=a.href)}),!0))})}var l=[{html:a("History Lists"),header:!0},{html:a("Saved Histories"),href:"histories/list",target:"_top"},{html:a("Histories Shared with Me"),href:"histories/list_shared",target:"_top"},{html:a("Current History"),header:!0,anon:!0},{html:a("Create New"),func:function(){Galaxy&&Galaxy.currHistoryPanel&&Galaxy.currHistoryPanel.createNewHistory()}},{html:a("Copy History"),func:function(){t(Galaxy.currHistoryPanel.model).done(function(){Galaxy.currHistoryPanel.loadCurrentHistory()})}},{html:a("Share or Publish"),href:"history/sharing"},{html:a("Show Structure"),href:"history/display_structured",anon:!0},{html:a("Extract Workflow"),href:"workflow/build_from_current_history"},{html:a("Delete"),anon:!0,func:function(){Galaxy&&Galaxy.currHistoryPanel&&confirm(a("Really delete the current history?"))&&Galaxy.currHistoryPanel.model._delete().done(function(){Galaxy.currHistoryPanel.loadCurrentHistory()})}},{html:a("Delete Permanently"),purge:!0,anon:!0,func:function(){Galaxy&&Galaxy.currHistoryPanel&&confirm(a("Really delete the current history permanently? This cannot be undone."))&&Galaxy.currHistoryPanel.model.purge().done(function(){Galaxy.currHistoryPanel.loadCurrentHistory()})}},{html:a("Dataset Actions"),header:!0,anon:!0},{html:a("Copy Datasets"),href:"dataset/copy_datasets"},{html:a("Dataset Security"),href:"root/history_set_default_permissions"},{html:a("Resume Paused Jobs"),href:"history/resume_paused_jobs?current=True",anon:!0},{html:a("Collapse Expanded Datasets"),func:function(){Galaxy&&Galaxy.currHistoryPanel&&Galaxy.currHistoryPanel.collapseAll()}},{html:a("Unhide Hidden Datasets"),anon:!0,func:function(){Galaxy&&Galaxy.currHistoryPanel&&confirm(a("Really unhide all hidden datasets?"))&&$.post(Galaxy.root+"history/adjust_hidden",{user_action:"unhide"},function(){Galaxy.currHistoryPanel.loadCurrentHistory()})}},{html:a("Delete Hidden Datasets"),anon:!0,func:function(){Galaxy&&Galaxy.currHistoryPanel&&confirm(a("Really delete all hidden datasets?"))&&$.post(Galaxy.root+"history/adjust_hidden",{user_action:"delete"},function(){Galaxy.currHistoryPanel.loadCurrentHistory()})}},{html:a("Purge Deleted Datasets"),confirm:a("Really delete all deleted datasets permanently? This cannot be undone."),href:"history/purge_deleted_datasets",purge:!0,anon:!0},{html:a("Downloads"),header:!0},{html:a("Export Tool Citations"),href:"history/citations",anon:!0},{html:a("Export History to File"),href:"history/export_archive?preview=True",anon:!0},{html:a("Other Actions"),header:!0},{html:a("Import from File"),href:"history/import_archive"}];o.add({url:"api/webhooks/history-menu/all",async:!1,callback:function(e){var t=[];$.each(e.models,function(e,r){var o=r.toJSON();o.activate&&t.push({html:a(o.config.title),anon:!0})}),t.length>0&&(t.unshift({html:a("Webhooks"),header:!0}),$.merge(l,t))}});return function(t,r){var a=n(void 0===(r=r||{}).anonymous||r.anonymous,r.purgeAllowed||!1,Galaxy.root);return new e(t,a)}});
//# sourceMappingURL=../../../maps/mvc/history/options-menu.js.map
