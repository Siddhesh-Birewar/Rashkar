import 'package:flutter/widgets.dart';

/// Supported screen breakpoint categories for CropNet AI.
///
/// - [mobile]: screen width < 600px
/// - [tablet]: screen width between 600px and 1024px (inclusive)
/// - [desktop]: screen width > 1024px
enum AppBreakpoint {
  mobile,
  tablet,
  desktop;

  bool get isMobile => this == AppBreakpoint.mobile;
  bool get isTablet => this == AppBreakpoint.tablet;
  bool get isDesktop => this == AppBreakpoint.desktop;
}

/// Breakpoint thresholds and utility helpers.
class AppBreakpoints {
  const AppBreakpoints._();

  /// Maximum width for mobile devices.
  static const double mobileMax = 599.99;

  /// Minimum width for tablet devices.
  static const double tabletMin = 600.0;

  /// Maximum width for tablet devices.
  static const double tabletMax = 1024.0;

  /// Minimum width for desktop devices.
  static const double desktopMin = 1024.01;

  /// Standard content max widths
  static const double maxContentWidthReadable = 800.0;
  static const double maxContentWidthStandard = 1200.0;
  static const double maxContentWidthWide = 1440.0;

  /// Determines the [AppBreakpoint] for a given pixel width.
  static AppBreakpoint fromWidth(double width) {
    if (width < tabletMin) {
      return AppBreakpoint.mobile;
    } else if (width <= tabletMax) {
      return AppBreakpoint.tablet;
    } else {
      return AppBreakpoint.desktop;
    }
  }

  /// Determines the [AppBreakpoint] for a given [BoxConstraints].
  static AppBreakpoint fromConstraints(BoxConstraints constraints) {
    return fromWidth(constraints.maxWidth);
  }

  /// Determines the [AppBreakpoint] from the active [BuildContext].
  static AppBreakpoint of(BuildContext context) {
    return fromWidth(MediaQuery.sizeOf(context).width);
  }
}

/// Selects a value based on the current active breakpoint from [BuildContext].
///
/// If [desktop] is null, it falls back to [tablet], then [mobile].
/// If [tablet] is null, it falls back to [mobile].
T responsiveValue<T>({
  required BuildContext context,
  required T mobile,
  T? tablet,
  T? desktop,
}) {
  final breakpoint = AppBreakpoints.of(context);
  switch (breakpoint) {
    case AppBreakpoint.mobile:
      return mobile;
    case AppBreakpoint.tablet:
      return tablet ?? mobile;
    case AppBreakpoint.desktop:
      return desktop ?? tablet ?? mobile;
  }
}

/// Selects a value based on a raw width (e.g., from [BoxConstraints.maxWidth]).
T responsiveValueFromWidth<T>({
  required double width,
  required T mobile,
  T? tablet,
  T? desktop,
}) {
  final breakpoint = AppBreakpoints.fromWidth(width);
  switch (breakpoint) {
    case AppBreakpoint.mobile:
      return mobile;
    case AppBreakpoint.tablet:
      return tablet ?? mobile;
    case AppBreakpoint.desktop:
      return desktop ?? tablet ?? mobile;
  }
}

/// Convenient responsive extensions on [BuildContext].
extension ResponsiveContextExtension on BuildContext {
  /// Current size of the screen.
  Size get screenSize => MediaQuery.sizeOf(this);

  /// Current width of the screen.
  double get screenWidth => MediaQuery.sizeOf(this).width;

  /// Current height of the screen.
  double get screenHeight => MediaQuery.sizeOf(this).height;

  /// The active [AppBreakpoint] for this context.
  AppBreakpoint get breakpoint => AppBreakpoints.of(this);

  /// True if current screen width is < 600px.
  bool get isMobile => breakpoint == AppBreakpoint.mobile;

  /// True if current screen width is between 600px and 1024px.
  bool get isTablet => breakpoint == AppBreakpoint.tablet;

  /// True if current screen width is > 1024px.
  bool get isDesktop => breakpoint == AppBreakpoint.desktop;

  /// Ergonomic shortcut for [responsiveValue].
  T responsiveValue<T>({
    required T mobile,
    T? tablet,
    T? desktop,
  }) =>
      responsiveValueFromWidth(
        width: screenWidth,
        mobile: mobile,
        tablet: tablet,
        desktop: desktop,
      );
}

/// Responsive extensions on [BoxConstraints].
extension ResponsiveConstraintsExtension on BoxConstraints {
  /// The [AppBreakpoint] represented by [maxWidth].
  AppBreakpoint get breakpoint => AppBreakpoints.fromConstraints(this);

  /// True if [maxWidth] is < 600px.
  bool get isMobile => maxWidth < AppBreakpoints.tabletMin;

  /// True if [maxWidth] is between 600px and 1024px.
  bool get isTablet =>
      maxWidth >= AppBreakpoints.tabletMin &&
      maxWidth <= AppBreakpoints.tabletMax;

  /// True if [maxWidth] is > 1024px.
  bool get isDesktop => maxWidth > AppBreakpoints.tabletMax;

  /// Evaluates a responsive value based on [maxWidth].
  T responsiveValue<T>({
    required T mobile,
    T? tablet,
    T? desktop,
  }) =>
      responsiveValueFromWidth(
        width: maxWidth,
        mobile: mobile,
        tablet: tablet,
        desktop: desktop,
      );
}
