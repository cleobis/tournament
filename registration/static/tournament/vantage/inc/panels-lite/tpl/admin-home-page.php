<?php
$install_url = self_admin_url( 'plugin-install.php?tab=plugin-information&amp;plugin=siteorigin-panels&amp;TB_iframe=true&amp;width=600&amp;height=550' );
$home = get_theme_mod( 'siteorigin_panels_home_page_enabled', siteorigin_panels_lite_setting('home-page-default') );
$toggle_url = wp_nonce_url(admin_url('admin-ajax.php?action=panels_lite_toggle&panels_new='.($home ? 0 : 1)), 'toggle_panels_home');

?>
<div class="wrap" id="panels-home-page">
	<div id="icon-index" class="icon32"><br></div>
	<h2>
		<?php echo esc_html( siteorigin_panels_lite_localization('home_page_title') ) ?>

		<a id="panels-toggle-switch" href="<?php echo esc_url($toggle_url) ?>" class="state-<?php echo $home ? 'on' : 'off' ?> subtle-move">
			<div class="on-text"><?php echo esc_html( siteorigin_panels_lite_localization('on_text') ) ?></div>
			<div class="off-text"><?php echo esc_html( siteorigin_panels_lite_localization('on_text') ) ?></div>
			<img src="<?php echo get_template_directory_uri() ?>/inc/panels-lite/css/images/handle.png" class="handle" />
		</a>
	</h2>

	<?php echo wpautop( siteorigin_panels_lite_localization('home_install_message') ) ?>
	<?php if($home) echo wpautop( siteorigin_panels_lite_localization('home_disable_message') ) ?>

	<p class="install-container">
		<a href="<?php echo esc_url($install_url) ?>" class="install thickbox"><?php echo esc_html( siteorigin_panels_lite_localization('install_plugin') ) ?></a>
	</p>
	
</div>