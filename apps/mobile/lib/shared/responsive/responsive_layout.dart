import 'package:flutter/widgets.dart';

import 'breakpoints.dart';

/// Builder callback for responsive layout widgets providing [BuildContext]
/// and [BoxConstraints].
typedef ResponsiveWidgetBuilder = Widget Function(
  BuildContext context,
  BoxConstraints constraints,
);

/// Sizing information provided to [ResponsiveBuilder].
class ResponsiveSizingInformation {
  /// The global screen size from [MediaQuery].
  final Size screenSize;

  /// The local box constraints from [LayoutBuilder].
  final BoxConstraints localConstraints;

  /// The active breakpoint computed for this layout.
  final AppBreakpoint breakpoint;

  const ResponsiveSizingInformation({
    required this.screenSize,
    required this.localConstraints,
    required this.breakpoint,
  });

  /// Whether the active breakpoint is [AppBreakpoint.mobile].
  bool get isMobile => breakpoint == AppBreakpoint.mobile;

  /// Whether the active breakpoint is [AppBreakpoint.tablet].
  bool get isTablet => breakpoint == AppBreakpoint.tablet;

  /// Whether the active breakpoint is [AppBreakpoint.desktop].
  bool get isDesktop => breakpoint == AppBreakpoint.desktop;

  /// Effective width considered for the breakpoint (local constraints maxWidth).
  double get width => localConstraints.maxWidth;

  /// Effective height considered for the breakpoint (local constraints maxHeight).
  double get height => localConstraints.maxHeight;
}

/// Builder callback for [ResponsiveBuilder] taking [ResponsiveSizingInformation].
typedef ResponsiveSizingBuilder = Widget Function(
  BuildContext context,
  ResponsiveSizingInformation sizingInfo,
);

/// A widget that conditionally builds different layouts based on screen or
/// constraint breakpoints.
///
/// If [useConstraints] is true, breakpoint calculations use the parent
/// [BoxConstraints.maxWidth]. Otherwise, they use [MediaQuery.sizeOf].
class ResponsiveLayout extends StatelessWidget {
  /// Builder for mobile screens (< 600px).
  final ResponsiveWidgetBuilder mobile;

  /// Builder for tablet screens (600px - 1024px).
  /// Falls back to [mobile] if null.
  final ResponsiveWidgetBuilder? tablet;

  /// Builder for desktop screens (> 1024px).
  /// Falls back to [tablet] or [mobile] if null.
  final ResponsiveWidgetBuilder? desktop;

  /// When true, breakpoints are calculated based on the parent [BoxConstraints]
  /// instead of the global [MediaQuery] screen width.
  final bool useConstraints;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    this.desktop,
    this.useConstraints = false,
  });

  /// Convenience factory for pre-built widgets instead of builder callbacks.
  factory ResponsiveLayout.value({
    Key? key,
    required Widget mobile,
    Widget? tablet,
    Widget? desktop,
    bool useConstraints,
  }) = _ResponsiveLayoutValue;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final breakpoint = useConstraints
            ? constraints.breakpoint
            : AppBreakpoints.of(context);

        switch (breakpoint) {
          case AppBreakpoint.mobile:
            return mobile(context, constraints);
          case AppBreakpoint.tablet:
            return (tablet ?? mobile)(context, constraints);
          case AppBreakpoint.desktop:
            return (desktop ?? tablet ?? mobile)(context, constraints);
        }
      },
    );
  }
}

class _ResponsiveLayoutValue extends ResponsiveLayout {
  _ResponsiveLayoutValue({
    super.key,
    required Widget mobile,
    Widget? tablet,
    Widget? desktop,
    super.useConstraints = false,
  }) : super(
          mobile: (_, __) => mobile,
          tablet: tablet != null ? (_, __) => tablet : null,
          desktop: desktop != null ? (_, __) => desktop : null,
        );
}

/// A flexible builder widget that provides a [ResponsiveSizingInformation]
/// instance with sizing details, breakpoints, and boolean helpers.
class ResponsiveBuilder extends StatelessWidget {
  /// The builder callback.
  final ResponsiveSizingBuilder builder;

  /// When true, the breakpoint is evaluated using local constraints width.
  /// When false, the breakpoint is evaluated using global screen width.
  final bool useConstraintsForBreakpoint;

  const ResponsiveBuilder({
    super.key,
    required this.builder,
    this.useConstraintsForBreakpoint = false,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final screenSize = MediaQuery.sizeOf(context);
        final breakpoint = useConstraintsForBreakpoint
            ? constraints.breakpoint
            : AppBreakpoints.of(context);

        final sizingInfo = ResponsiveSizingInformation(
          screenSize: screenSize,
          localConstraints: constraints,
          breakpoint: breakpoint,
        );

        return builder(context, sizingInfo);
      },
    );
  }
}
