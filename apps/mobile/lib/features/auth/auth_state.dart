import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'auth_service.dart';

/// Reactive authentication state notifier observing Supabase session changes.
class AuthStateNotifier extends ChangeNotifier {
  static final AuthStateNotifier instance = AuthStateNotifier._internal();
  AuthStateNotifier._internal();

  StreamSubscription<AuthState>? _subscription;
  bool _isAuthenticated = false;
  User? _currentUser;
  bool _isLoading = true;

  bool get isAuthenticated => _isAuthenticated;
  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;

  /// Initialize state from current session and register listener.
  void initialize() {
    final authService = AuthService.instance;
    _isAuthenticated = authService.isAuthenticated;
    _currentUser = authService.currentUser;
    _isLoading = false;

    _subscription?.cancel();
    _subscription = authService.onAuthStateChange.listen((state) {
      _isAuthenticated = state.session != null;
      _currentUser = state.session?.user;
      notifyListeners();
    });
    notifyListeners();
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }
}
