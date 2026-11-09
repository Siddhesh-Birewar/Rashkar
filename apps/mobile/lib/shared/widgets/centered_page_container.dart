import 'package:flutter/widgets.dart';

import '../responsive/breakpoints.dart';
import 'app_spacing.dart';

/// A presentation container that horizontally centers its child with configurable
/// max-width constraints and responsive horizontal & vertical padding.
///
/// Ensures content looks readable and well-proportioned on wide desktop monitors
/// while gracefully adapting to tablets and smartphones.
class CenteredPageContainer extends StatelessWidget {
  /// The widget below this widget in the tree.
  final Widget child;

  /// Maximum allowed width for the inner content.
  /// Defaults to [AppBreakpoints.maxContentWidthStandard] (1200px).
  final double maxWidth;

  /// Explicit padding around the content.
  /// If null, defaults to [AppSpacing.pagePadding(context)].
  final EdgeInsetsGeometry? padding;

  /// Alignment of the content within the available space.
  /// Defaults to [Alignment.topCenter].
  final AlignmentGeometry alignment;

  /// Whether to wrap the content in a [SingleChildScrollView].
  /// Defaults to false.
  final bool scrollable;

  /// Scroll physics when [scrollable] is true.
  final ScrollPhysics? physics;

  /// Scroll controller when [scrollable] is true.
  final ScrollController? controller;

  /// Whether to wrap content in a [SafeArea].
  /// Defaults to false.
  final bool useSafeArea;

  /// Optional background color for the outer container.
  final Color? backgroundColor;

  const CenteredPageContainer({
    super.key,
    required this.child,
    this.maxWidth = AppBreakpoints.maxContentWidthStandard,
    this.padding,
    this.alignment = Alignment.topCenter,
    this.scrollable = false,
    this.physics,
    this.controller,
    this.useSafeArea = false,
    this.backgroundColor,
  });

  /// Factory for narrower reading or form-focused content (max width 800px).
  const CenteredPageContainer.readable({
    super.key,
    required this.child,
    this.padding,
    this.alignment = Alignment.topCenter,
    this.scrollable = false,
    this.physics,
    this.controller,
    this.useSafeArea = false,
    this.backgroundColor,
  }) : maxWidth = AppBreakpoints.maxContentWidthReadable;

  /// Factory for wide analytics/dashboards (max width 1440px).
  const CenteredPageContainer.wide({
    super.key,
    required this.child,
    this.padding,
    this.alignment = Alignment.topCenter,
    this.scrollable = false,
    this.physics,
    this.controller,
    this.useSafeArea = false,
    this.backgroundColor,
  }) : maxWidth = AppBreakpoints.maxContentWidthWide;

  @override
  Widget build(BuildContext context) {
    final effectivePadding = padding ?? AppSpacing.pagePadding(context);

    Widget content = ConstrainedBox(
      constraints: BoxConstraints(maxWidth: maxWidth),
      child: Padding(
        padding: effectivePadding,
        child: child,
      ),
    );

    if (scrollable) {
      content = SingleChildScrollView(
        controller: controller,
        physics: physics,
        child: Align(
          alignment: alignment,
          child: content,
        ),
      );
    } else {
      content = Align(
        alignment: alignment,
        child: content,
      );
    }

    if (useSafeArea) {
      content = SafeArea(child: content);
    }

    if (backgroundColor != null) {
      content = ColoredBox(
        color: backgroundColor!,
        child: content,
      );
    }

    return content;
  }
}

/// Sliver variant of [CenteredPageContainer] for use in [CustomScrollView].
class CenteredSliverPageContainer extends StatelessWidget {
  final Widget child;
  final double maxWidth;
  final EdgeInsetsGeometry? padding;

  const CenteredSliverPageContainer({
    super.key,
    required this.child,
    this.maxWidth = AppBreakpoints.maxContentWidthStandard,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final effectivePadding = padding ?? AppSpacing.pagePadding(context);

    return SliverToBoxAdapter(
      child: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: Padding(
            padding: effectivePadding,
            child: child,
          ),
        ),
      ),
    );
  }
}
