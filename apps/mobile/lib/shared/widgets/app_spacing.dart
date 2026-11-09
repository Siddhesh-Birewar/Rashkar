import 'package:flutter/widgets.dart';

import '../responsive/breakpoints.dart';

/// Design tokens for spacing, padding, and layout dimensions across CropNet AI.
class AppSpacing {
  const AppSpacing._();

  // Spacing scalar values
  static const double zero = 0.0;
  static const double xxs = 2.0;
  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 16.0;
  static const double lg = 24.0;
  static const double xl = 32.0;
  static const double xxl = 48.0;
  static const double xxxl = 64.0;

  // Sized box spacers (Vertical)
  static const Widget verticalSpaceXXS = SizedBox(height: xxs);
  static const Widget verticalSpaceXS = SizedBox(height: xs);
  static const Widget verticalSpaceSM = SizedBox(height: sm);
  static const Widget verticalSpaceMD = SizedBox(height: md);
  static const Widget verticalSpaceLG = SizedBox(height: lg);
  static const Widget verticalSpaceXL = SizedBox(height: xl);
  static const Widget verticalSpaceXXL = SizedBox(height: xxl);
  static const Widget verticalSpaceXXXL = SizedBox(height: xxxl);

  // Sized box spacers (Horizontal)
  static const Widget horizontalSpaceXXS = SizedBox(width: xxs);
  static const Widget horizontalSpaceXS = SizedBox(width: xs);
  static const Widget horizontalSpaceSM = SizedBox(width: sm);
  static const Widget horizontalSpaceMD = SizedBox(width: md);
  static const Widget horizontalSpaceLG = SizedBox(width: lg);
  static const Widget horizontalSpaceXL = SizedBox(width: xl);
  static const Widget horizontalSpaceXXL = SizedBox(width: xxl);
  static const Widget horizontalSpaceXXXL = SizedBox(width: xxxl);

  // Uniform EdgeInsets
  static const EdgeInsets paddingZero = EdgeInsets.zero;
  static const EdgeInsets paddingAllXXS = EdgeInsets.all(xxs);
  static const EdgeInsets paddingAllXS = EdgeInsets.all(xs);
  static const EdgeInsets paddingAllSM = EdgeInsets.all(sm);
  static const EdgeInsets paddingAllMD = EdgeInsets.all(md);
  static const EdgeInsets paddingAllLG = EdgeInsets.all(lg);
  static const EdgeInsets paddingAllXL = EdgeInsets.all(xl);
  static const EdgeInsets paddingAllXXL = EdgeInsets.all(xxl);

  // Symmetric Horizontal EdgeInsets
  static const EdgeInsets paddingHorizontalXS = EdgeInsets.symmetric(horizontal: xs);
  static const EdgeInsets paddingHorizontalSM = EdgeInsets.symmetric(horizontal: sm);
  static const EdgeInsets paddingHorizontalMD = EdgeInsets.symmetric(horizontal: md);
  static const EdgeInsets paddingHorizontalLG = EdgeInsets.symmetric(horizontal: lg);
  static const EdgeInsets paddingHorizontalXL = EdgeInsets.symmetric(horizontal: xl);

  // Symmetric Vertical EdgeInsets
  static const EdgeInsets paddingVerticalXS = EdgeInsets.symmetric(vertical: xs);
  static const EdgeInsets paddingVerticalSM = EdgeInsets.symmetric(vertical: sm);
  static const EdgeInsets paddingVerticalMD = EdgeInsets.symmetric(vertical: md);
  static const EdgeInsets paddingVerticalLG = EdgeInsets.symmetric(vertical: lg);
  static const EdgeInsets paddingVerticalXL = EdgeInsets.symmetric(vertical: xl);

  /// Computes responsive horizontal page padding:
  /// - Mobile: 16.0
  /// - Tablet: 24.0
  /// - Desktop: 32.0
  static double pageHorizontalPadding(BuildContext context) {
    return responsiveValue<double>(
      context: context,
      mobile: md,
      tablet: lg,
      desktop: xl,
    );
  }

  /// Computes responsive vertical page padding:
  /// - Mobile: 16.0
  /// - Tablet: 20.0
  /// - Desktop: 24.0
  static double pageVerticalPadding(BuildContext context) {
    return responsiveValue<double>(
      context: context,
      mobile: md,
      tablet: 20.0,
      desktop: lg,
    );
  }

  /// Full page responsive padding combining horizontal and vertical values.
  static EdgeInsets pagePadding(BuildContext context) {
    return EdgeInsets.symmetric(
      horizontal: pageHorizontalPadding(context),
      vertical: pageVerticalPadding(context),
    );
  }

  /// Responsive card internal padding.
  static EdgeInsets cardPadding(BuildContext context) {
    return EdgeInsets.all(
      responsiveValue<double>(
        context: context,
        mobile: md,
        tablet: 20.0,
        desktop: lg,
      ),
    );
  }
}
