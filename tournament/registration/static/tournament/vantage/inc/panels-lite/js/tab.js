jQuery(function($){
    // This is the part where we move the panels box into a tab of the content editor
    $( '#wp-content-editor-tools .wp-editor-tabs' )
        .append(
        $( '<a id="content-panels" target="_blank" class="hide-if-no-js wp-switch-editor switch-panels thickbox"></a>' )
            .html( panelsLiteTeaser.tab )
            .attr( 'href', panelsLiteTeaser.installUrl )
            .css( 'text-decoration', 'none' )
    );
});