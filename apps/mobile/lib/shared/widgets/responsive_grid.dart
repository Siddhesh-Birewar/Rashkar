import 'package:flutter/widgets.dart';

import '../responsive/breakpoints.dart';
import 'app_spacing.dart';

/// Adaptive grid layout for cards and metrics that gracefully wraps
/// from 1 column on mobile, 2 columns on tablet, to 3-4 columns on desktop.
class ResponsiveGrid extends StatelessWidget {
  /// The children widgets to display in the grid.
  final List<Widget> children;

  /// Number of columns on mobile screens (< 600px). Defaults to 1.
  final int mobileColumns;

  /// Number of columns on tablet screens (600px - 1024px). Defaults to 2.
  final int tabletColumns;

  /// Number of columns on desktop screens (> 1024px). Defaults to 3.
  final int desktopColumns;

  /// Horizontal spacing between items. Defaults to [AppSpacing.md] (16px).
  final double spacing;

  /// Vertical run spacing between rows. Defaults to [AppSpacing.md] (16px).
  final double runSpacing;

  /// Alignment of children within runs.
  final WrapAlignment alignment;

  /// Cross-axis alignment of children within runs.
  final WrapCrossAlignment crossAxisAlignment;

  /// When true (default), column counts are evaluated using local
  /// [BoxConstraints.maxWidth]. When false, global [MediaQuery] width is used.
  final bool useConstraints;

  const ResponsiveGrid({
    super.key,
    required this.children,
    this.mobileColumns = 1,
    this.tabletColumns = 2,
    this.desktopColumns = 3,
    this.spacing = AppSpacing.md,
    this.runSpacing = AppSpacing.md,
    this.alignment = WrapAlignment.start,
    this.crossAxisAlignment = WrapCrossAlignment.start,
    this.useConstraints = true,
  });

  /// 4-column desktop variant for metric and status cards.
  const ResponsiveGrid.metrics({
    super.key,
    required this.children,
    this.mobileColumns = 1,
    this.tabletColumns = 2,
    this.desktopColumns = 4,
    this.spacing = AppSpacing.md,
    this.runSpacing = AppSpacing.md,
    this.alignment = WrapAlignment.start,
    this.crossAxisAlignment = WrapCrossAlignment.start,
    this.useConstraints = true,
  });

  int _calculateColumns(double width) {
    if (width < AppBreakpoints.tabletMin) {
      return mobileColumns;
    } else if (width <= AppBreakpoints.tabletMax) {
      return tabletColumns;
    } else {
      return desktopColumns;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (children.isEmpty) {
      return const SizedBox.shrink();
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final activeWidth = useConstraints
            ? constraints.maxWidth
            : MediaQuery.sizeOf(context).width;

        final columns = _calculateColumns(activeWidth).clamp(1, 12);

        // Compute exact item width so items evenly span the available width.
        final totalSpacing = (columns - 1) * spacing;
        final availableWidth = constraints.maxWidth.isFinite
            ? constraints.maxWidth
            : activeWidth;
        final itemWidth = ((availableWidth - totalSpacing) / columns).clamp(0.0, double.infinity);

        return Wrap(
          spacing: spacing,
          runSpacing: runSpacing,
          alignment: alignment,
          crossAxisAlignment: crossAxisAlignment,
          children: children.map((child) {
            return SizedBox(
              width: itemWidth,
              child: child,
            );
          }).toList(),
        );
      },
    );
  }
}

/// Scrollable responsive grid view that adapts column count across breakpoints.
class ResponsiveGridView extends StatelessWidget {
  final int itemCount;
  final NullableIndexedWidgetBuilder itemBuilder;
  final int mobileColumns;
  final int tabletColumns;
  final int desktopColumns;
  final double spacing;
  final double runSpacing;
  final double childAspectRatio;
  final EdgeInsetsGeometry? padding;
  final bool shrinkWrap;
  final ScrollPhysics? physics;
  final ScrollController? controller;
  final bool useConstraints;

  const ResponsiveGridView.builder({
    super.key,
    required this.itemCount,
    required this.itemBuilder,
    this.mobileColumns = 1,
    this.tabletColumns = 2,
    this.desktopColumns = 3,
    this.spacing = AppSpacing.md,
    this.runSpacing = AppSpacing.md,
    this.childAspectRatio = 1.0,
    this.padding,
    this.shrinkWrap = false,
    this.physics,
    this.controller,
    this.useConstraints = true,
  });

  int _calculateColumns(double width) {
    if (width < AppBreakpoints.tabletMin) {
      return mobileColumns;
    } else if (width <= AppBreakpoints.tabletMax) {
      return tabletColumns;
    } else {
      return desktopColumns;
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final activeWidth = useConstraints
            ? constraints.maxWidth
            : MediaQuery.sizeOf(context).width;

        final columns = _calculateColumns(activeWidth).clamp(1, 12);

        return GridView.builder(
          key: key,
          itemCount: itemCount,
          padding: padding,
          shrinkWrap: shrinkWrap,
          physics: physics,
          controller: controller,
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: columns,
            crossAxisSpacing: spacing,
            mainAxisSpacing: runSpacing,
            childAspectRatio: childAspectRatio,
          ),
          itemBuilder: itemBuilder,
        );
      },
    );
  }
}

/// A 12-column grid item for [ResponsiveGridRow].
class ResponsiveGridCol {
  /// Columns spanned on mobile (< 600px). Out of 12.
  final int mobile;

  /// Columns spanned on tablet (600px - 1024px). Out of 12.
  /// Defaults to [mobile].
  final int? tablet;

  /// Columns spanned on desktop (> 1024px). Out of 12.
  /// Defaults to [tablet] or [mobile].
  final int? desktop;

  /// The widget content for this column.
  final Widget child;

  const ResponsiveGridCol({
    this.mobile = 12,
    this.tablet,
    this.desktop,
    required this.child,
  });

  int getSpan(AppBreakpoint breakpoint) {
    switch (breakpoint) {
      case AppBreakpoint.mobile:
        return mobile.clamp(1, 12);
      case AppBreakpoint.tablet:
        return (tablet ?? mobile).clamp(1, 12);
      case AppBreakpoint.desktop:
        return (desktop ?? tablet ?? mobile).clamp(1, 12);
    }
  }
}

/// A 12-column grid row layout that sizes each [ResponsiveGridCol] according
/// to its responsive span.
class ResponsiveGridRow extends StatelessWidget {
  final List<ResponsiveGridCol> children;
  final double spacing;
  final double runSpacing;
  final bool useConstraints;

  const ResponsiveGridRow({
    super.key,
    required this.children,
    this.spacing = AppSpacing.md,
    this.runSpacing = AppSpacing.md,
    this.useConstraints = true,
  });

  @override
  Widget build(BuildContext context) {
    if (children.isEmpty) {
      return const SizedBox.shrink();
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final activeWidth = useConstraints
            ? constraints.maxWidth
            : MediaQuery.sizeOf(context).width;

        final breakpoint = AppBreakpoints.fromWidth(activeWidth);
        final availableWidth = constraints.maxWidth.isFinite
            ? constraints.maxWidth
            : activeWidth;

        return Wrap(
          spacing: spacing,
          runSpacing: runSpacing,
          children: children.map((col) {
            final span = col.getSpan(breakpoint);
            // In a 12-column grid:
            // If span == 12, it takes the entire available width.
            // If span < 12, width is proportional minus inter-column spacing.
            final fraction = span / 12.0;
            // Approximate width taking spacing into account
            final colWidth = span == 12
                ? availableWidth
                : ((availableWidth - (12 / span - 1) * spacing) * fraction)
                    .clamp(0.0, availableWidth);

            return SizedBox(
              width: colWidth,
              child: col.child,
            );
          }).toList(),
        );
      },
    );
  }
}
