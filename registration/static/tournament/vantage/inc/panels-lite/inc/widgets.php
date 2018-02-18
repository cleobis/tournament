<?php

/**
 * Render any missing widgets that Page Builder will eventually provide
 *
 * @param $code
 * @param $widget
 * @param $args
 * @param $instance
 *
 * @return string
 */
function siteorigin_panels_lite_missing_widget($code, $widget, $args , $instance){
	switch($widget) {
		case 'SiteOrigin_Panels_Widgets_PostLoop':
			ob_start();
			SiteOrigin_Panels_Lite_Missing_Widgets::postloop($args, $instance);
			$code = ob_get_clean();
			break;

		case 'WP_Widget_Black_Studio_TinyMCE':
			ob_start();
			SiteOrigin_Panels_Lite_Missing_Widgets::visual_editor($args, $instance);
			$code = ob_get_clean();
			break;
	}

	return $code;
}
add_filter('siteorigin_panels_missing_widget', 'siteorigin_panels_lite_missing_widget', 5, 4);

/**
 * Class that handles all the basic missing widget rendering.
 *
 * Class SiteOrigin_Panels_Lite_Missing_Widgets
 */
class SiteOrigin_Panels_Lite_Missing_Widgets {

	static function postloop( $args, $instance ){
		if( empty($instance['template']) ) return;
		if( is_admin() ) return;

		echo $args['before_widget'];

		$instance['title'] = apply_filters('widget_title', $instance['title'], $instance, 'siteorigin-panels-postloop');
		if ( !empty( $instance['title'] ) ) {
			echo $args['before_title'] . $instance['title'] . $args['after_title'];
		}

		if(strpos('/'.$instance['template'], '/content') !== false) {
			while(have_posts()) {
				the_post();
				locate_template($instance['template'], true, false);
			}
		}
		else {
			locate_template($instance['template'], true, false);
		}

		echo $args['after_widget'];

		// Reset everything
		rewind_posts();
		wp_reset_postdata();
	}

	static function visual_editor( $args, $instance  ){
		$before_widget = $args['before_widget'];
		$after_widget = $args['after_widget'];
		$before_title = $args['before_title'];
		$after_title = $args['after_title'];
		$before_text = apply_filters( 'black_studio_tinymce_before_text', '<div class="textwidget">', $instance );
		$after_text = apply_filters( 'black_studio_tinymce_after_text', '</div>', $instance );
		$title = apply_filters( 'widget_title', empty( $instance['title'] ) ? '' : $instance['title'], $instance, false );
		$text = apply_filters( 'widget_text', empty( $instance['text'] ) ? '' : $instance['text'], $instance, false );
		$hide_empty = apply_filters( 'black_studio_tinymce_hide_empty', false, $instance );
		if ( ! ( $hide_empty && empty( $text ) ) ) {
			$output = $before_widget;
			if ( ! empty( $title ) ) {
				$output .= $before_title . $title . $after_title;
			}
			$output .= $before_text . $text . $after_text;
			$output .= $after_widget;
			echo $output; // xss ok
		}
	}
}