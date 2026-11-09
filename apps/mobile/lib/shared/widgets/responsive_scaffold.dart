import 'package:flutter/material.dart';

import '../responsive/breakpoints.dart';

/// Destination item for [ResponsiveScaffold].
class ResponsiveScaffoldDestination {
  /// The icon widget shown for this destination.
  final Widget icon;

  /// Optional icon widget shown when destination is selected.
  final Widget? selectedIcon;

  /// Label string describing the destination.
  final String label;

  /// Optional tooltip message.
  final String? tooltip;

  /// Optional badge widget displayed over the icon.
  final Widget? badge;

  const ResponsiveScaffoldDestination({
    required this.icon,
    this.selectedIcon,
    required this.label,
    this.tooltip,
    this.badge,
  });
}

/// Adaptive shell scaffold supporting responsive navigation presentation.
///
/// Automatically switches between:
/// - A bottom [NavigationBar] on mobile screens (< 600px).
/// - A persistent side [NavigationRail] on tablet and desktop screens (>= 600px).
/// - Optionally expands the [NavigationRail] on wide desktop screens to show
///   labels beside icons.
class ResponsiveScaffold extends StatelessWidget {
  /// Currently selected destination index.
  final int currentIndex;

  /// Callback when a navigation destination is tapped.
  final ValueChanged<int>? onNavigationIndexChanged;

  /// List of navigation destinations.
  final List<ResponsiveScaffoldDestination> destinations;

  /// Primary screen content.
  final Widget body;

  /// Optional top app bar.
  final PreferredSizeWidget? appBar;

  /// Optional floating action button.
  final Widget? floatingActionButton;

  /// Location of the floating action button.
  final FloatingActionButtonLocation? floatingActionButtonLocation;

  /// Optional navigation drawer.
  final Widget? drawer;

  /// Optional end drawer.
  final Widget? endDrawer;

  /// Scaffold background color.
  final Color? backgroundColor;

  /// Leading widget displayed at the top of the [NavigationRail] (e.g. app logo).
  final Widget? railLeading;

  /// Trailing widget displayed at the bottom of the [NavigationRail] (e.g. user profile / settings).
  final Widget? railTrailing;

  /// Explicitly override whether the [NavigationRail] is extended.
  /// If null, automatically extends on desktop screens with width >= 1200px.
  final bool? railExtended;

  /// Label type when the [NavigationRail] is collapsed.
  /// Defaults to [NavigationRailLabelType.all].
  final NavigationRailLabelType? railLabelType;

  /// Minimum width of the collapsed rail (default 72.0).
  final double railMinWidth;

  /// Minimum width of the extended rail (default 240.0).
  final double railExtendedWidth;

  /// Background color of the [NavigationRail].
  final Color? railBackgroundColor;

  /// Elevation of the [NavigationRail].
  final double? railElevation;

  /// Whether to avoid bottom inset.
  final bool? resizeToAvoidBottomInset;

  const ResponsiveScaffold({
    super.key,
    required this.currentIndex,
    required this.destinations,
    required this.body,
    this.onNavigationIndexChanged,
    this.appBar,
    this.floatingActionButton,
    this.floatingActionButtonLocation,
    this.drawer,
    this.endDrawer,
    this.backgroundColor,
    this.railLeading,
    this.railTrailing,
    this.railExtended,
    this.railLabelType,
    this.railMinWidth = 72.0,
    this.railExtendedWidth = 240.0,
    this.railBackgroundColor,
    this.railElevation,
    this.resizeToAvoidBottomInset,
  });

  @override
  Widget build(BuildContext context) {
    final isMobile = context.isMobile;

    if (isMobile) {
      return Scaffold(
        appBar: appBar,
        body: body,
        drawer: drawer,
        endDrawer: endDrawer,
        floatingActionButton: floatingActionButton,
        floatingActionButtonLocation: floatingActionButtonLocation,
        backgroundColor: backgroundColor,
        resizeToAvoidBottomInset: resizeToAvoidBottomInset,
        bottomNavigationBar: destinations.isNotEmpty
            ? NavigationBar(
                selectedIndex: currentIndex,
                onDestinationSelected: onNavigationIndexChanged,
                destinations: destinations.map((d) {
                  return NavigationDestination(
                    icon: d.badge != null ? Badge(child: d.icon) : d.icon,
                    selectedIcon: d.selectedIcon != null
                        ? (d.badge != null
                            ? Badge(child: d.selectedIcon!)
                            : d.selectedIcon!)
                        : null,
                    label: d.label,
                    tooltip: d.tooltip,
                  );
                }).toList(),
              )
            : null,
      );
    }

    // Tablet & Desktop Layout with persistent side NavigationRail
    final shouldExtend = railExtended ?? (context.screenWidth >= 1200);

    // Flutter requires labelType to be none/null when extended is true.
    final effectiveLabelType = shouldExtend
        ? NavigationRailLabelType.none
        : (railLabelType ?? NavigationRailLabelType.all);

    return Scaffold(
      backgroundColor: backgroundColor,
      drawer: drawer,
      endDrawer: endDrawer,
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      body: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (destinations.isNotEmpty) ...[
            NavigationRail(
              selectedIndex: currentIndex,
              onDestinationSelected: onNavigationIndexChanged,
              extended: shouldExtend,
              labelType: effectiveLabelType,
              minWidth: railMinWidth,
              minExtendedWidth: railExtendedWidth,
              backgroundColor: railBackgroundColor,
              elevation: railElevation,
              leading: railLeading,
              trailing: railTrailing != null
                  ? Expanded(
                      child: Align(
                        alignment: Alignment.bottomCenter,
                        child: Padding(
                          padding: const EdgeInsets.only(bottom: 16.0),
                          child: railTrailing!,
                        ),
                      ),
                    )
                  : null,
              destinations: destinations.map((d) {
                return NavigationRailDestination(
                  icon: d.badge != null ? Badge(child: d.icon) : d.icon,
                  selectedIcon: d.selectedIcon != null
                      ? (d.badge != null
                          ? Badge(child: d.selectedIcon!)
                          : d.selectedIcon!)
                      : null,
                  label: Text(d.label),
                  padding: const EdgeInsets.symmetric(vertical: 6.0),
                );
              }).toList(),
            ),
            const VerticalDivider(thickness: 1, width: 1),
          ],
          Expanded(
            child: Scaffold(
              appBar: appBar,
              body: body,
              floatingActionButton: floatingActionButton,
              floatingActionButtonLocation: floatingActionButtonLocation,
              backgroundColor: backgroundColor,
            ),
          ),
        ],
      ),
    );
  }
}
