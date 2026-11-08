import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'screens/heat_safety_screen.dart';
import 'screens/farm_registration_screen.dart';
import 'localization/app_localizations.dart';

void main() {
  runApp(const RashkarFarmerApp());
}

class RashkarFarmerApp extends StatefulWidget {
  const RashkarFarmerApp({Key? key}) : super(key: key);

  @override
  State<RashkarFarmerApp> createState() => _RashkarFarmerAppState();
}

class _RashkarFarmerAppState extends State<RashkarFarmerApp> {
  String _currentLanguage = 'mr'; // Default Marathi for Maharashtra farmers

  void _toggleLanguage() {
    setState(() {
      _currentLanguage = _currentLanguage == 'mr' ? 'en' : 'mr';
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Rashkar Krishi',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2E7D32),
          primary: const Color(0xFF2E7D32),
          secondary: const Color(0xFFD84315),
        ),
        fontFamily: 'Roboto',
        textTheme: const TextTheme(
          bodyLarge: TextStyle(fontSize: 16.0),
          bodyMedium: TextStyle(fontSize: 14.0),
        ),
      ),
      home: MainNavigationShell(
        lang: _currentLanguage,
        onToggleLang: _toggleLanguage,
      ),
    );
  }
}

class MainNavigationShell extends StatefulWidget {
  final String lang;
  final VoidCallback onToggleLang;

  const MainNavigationShell({
    Key? key,
    required this.lang,
    required this.onToggleLang,
  }) : super(key: key);

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final lang = widget.lang;

    final screens = [
      DashboardScreen(
        lang: lang,
        onToggleLang: widget.onToggleLang,
      ),
      HeatSafetyScreen(lang: lang),
      FarmRegistrationScreen(lang: lang),
    ];

    return Scaffold(
      body: screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() => _currentIndex = index);
        },
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.agriculture_outlined),
            selectedIcon: const Icon(Icons.agriculture),
            label: AppStrings.get('nav_dashboard', lang: lang),
          ),
          NavigationDestination(
            icon: const Icon(Icons.warning_amber_rounded),
            selectedIcon: const Icon(Icons.warning),
            label: AppStrings.get('nav_heat_safety', lang: lang),
          ),
          NavigationDestination(
            icon: const Icon(Icons.add_location_alt_outlined),
            selectedIcon: const Icon(Icons.add_location_alt),
            label: AppStrings.get('nav_farm', lang: lang),
          ),
        ],
      ),
    );
  }
}
