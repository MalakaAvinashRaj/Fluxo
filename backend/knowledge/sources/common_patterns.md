## StatelessWidget Boilerplate

```dart
import 'package:flutter/material.dart';

class MyWidget extends StatelessWidget {
  final String title;
  final String? subtitle;
  final VoidCallback? onTap;

  const MyWidget({
    super.key,               // Flutter 3.x shorthand for Key? key
    required this.title,
    this.subtitle,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          if (subtitle != null)   // conditional widget
            Text(
              subtitle!,
              style: Theme.of(context).textTheme.bodySmall,
            ),
        ],
      ),
    );
  }
}
```

---

## StatefulWidget Boilerplate

```dart
import 'package:flutter/material.dart';

class CounterScreen extends StatefulWidget {
  final String title;
  final int initialCount;

  const CounterScreen({
    super.key,
    required this.title,
    this.initialCount = 0,
  });

  @override
  State<CounterScreen> createState() => _CounterScreenState();
}

class _CounterScreenState extends State<CounterScreen> {
  // State variables
  late int _count;
  bool _isLoading = false;

  // Called once when widget is inserted into tree
  @override
  void initState() {
    super.initState();
    _count = widget.initialCount;   // access widget props via `widget`
    _loadData();
  }

  // Called whenever widget config changes (parent rebuilds with new props)
  @override
  void didUpdateWidget(CounterScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialCount != widget.initialCount) {
      _count = widget.initialCount;
    }
  }

  // Called when dependencies (InheritedWidgets) change
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Safe to access context-dependent things here
  }

  // Cleanup resources
  @override
  void dispose() {
    // Cancel controllers, subscriptions, animation controllers here
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      await Future.delayed(Duration(seconds: 1));
      // fetch data...
    } catch (e) {
      // handle error
    } finally {
      // Check if widget is still mounted before calling setState
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _increment() {
    setState(() {
      _count++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : Center(
              child: Text(
                '$_count',
                style: Theme.of(context).textTheme.displayLarge,
              ),
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _increment,
        child: Icon(Icons.add),
      ),
    );
  }
}
```

---

## setState Usage & Best Practices

```dart
// ✅ GOOD — minimal setState, put only state changes inside
void _updateUser(User newUser) {
  final processed = processUser(newUser);  // do work OUTSIDE setState
  setState(() {
    _user = processed;
  });
}

// ❌ BAD — heavy work inside setState
void _updateUserBad(User newUser) {
  setState(() {
    _user = processUser(newUser);   // processUser is expensive
    _stats = calculateStats(_user); // extra work slows down rebuild
  });
}

// ✅ GOOD — multiple state changes in one setState call
void _reset() {
  setState(() {
    _count = 0;
    _isLoading = false;
    _errorMessage = null;
  });
}

// ❌ BAD — multiple setState calls triggers multiple rebuilds
void _resetBad() {
  setState(() => _count = 0);
  setState(() => _isLoading = false);
  setState(() => _errorMessage = null);
}

// ✅ GOOD — check mounted before setState in async functions
Future<void> _fetchData() async {
  setState(() => _isLoading = true);
  try {
    final data = await repository.fetchData();
    if (mounted) {   // IMPORTANT: widget may have been disposed
      setState(() {
        _data = data;
        _isLoading = false;
      });
    }
  } catch (e) {
    if (mounted) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }
}

// ✅ GOOD — using a local variable to reduce state
// Instead of storing derived values, compute them in build()
@override
Widget build(BuildContext context) {
  final total = _items.fold(0.0, (sum, item) => sum + item.price);  // derived
  return Text('Total: \$${total.toStringAsFixed(2)}');
}
```

---

## Lifecycle Methods

```dart
// Full lifecycle overview
class LifecycleWidget extends StatefulWidget {
  @override
  State<LifecycleWidget> createState() => _LifecycleWidgetState();
}

class _LifecycleWidgetState extends State<LifecycleWidget>
    with WidgetsBindingObserver {

  @override
  void initState() {
    super.initState();
    // ✅ Called ONCE. Safe for: initializing controllers, fetching initial data,
    //    setting up listeners. Context is NOT fully ready here — don't use it.
    WidgetsBinding.instance.addObserver(this);  // observe app lifecycle
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Runs after first frame — context is fully ready here
      _showWelcomeDialog();
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // ✅ Called after initState AND whenever an InheritedWidget changes.
    //    Safe to use context-dependent APIs like MediaQuery, Theme, Provider.
  }

  @override
  void build(BuildContext context) {
    // ✅ Called whenever setState is triggered or parent rebuilds.
    //    Keep this pure — no side effects here.
  }

  @override
  void didUpdateWidget(LifecycleWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    // ✅ Called when parent widget rebuilds with new props.
    //    Compare old vs new to decide if internal state needs update.
  }

  @override
  void deactivate() {
    super.deactivate();
    // ✅ Called when widget is temporarily removed from tree
    //    (e.g., navigating away). May be reinserted later.
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    // ✅ Called ONCE before widget is permanently removed.
    //    MUST dispose: controllers, streams, animation controllers,
    //    timers, focus nodes, scroll controllers.
    super.dispose();
  }

  // App lifecycle (requires WidgetsBindingObserver mixin)
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    switch (state) {
      case AppLifecycleState.resumed:
        // App is in foreground and responding to user input
        break;
      case AppLifecycleState.inactive:
        // App is in transition (phone call, split screen, etc.)
        break;
      case AppLifecycleState.paused:
        // App is in background — save data, pause animations
        break;
      case AppLifecycleState.detached:
        // App is about to be killed
        break;
      case AppLifecycleState.hidden:
        // App is hidden (Flutter 3.13+)
        break;
    }
  }
}
```

---

## InheritedWidget & Provider Pattern

### Basic InheritedWidget
```dart
class AppState extends InheritedWidget {
  final int counter;
  final VoidCallback increment;

  const AppState({
    super.key,
    required this.counter,
    required this.increment,
    required super.child,
  });

  // Static helper for easy access
  static AppState of(BuildContext context) {
    final result = context.dependOnInheritedWidgetOfExactType<AppState>();
    assert(result != null, 'No AppState found in context');
    return result!;
  }

  @override
  bool updateShouldNotify(AppState oldWidget) {
    return counter != oldWidget.counter;
  }
}

// Usage
final state = AppState.of(context);
Text('${state.counter}')
ElevatedButton(onPressed: state.increment, child: Text('Increment'))
```

---

## Navigation Patterns

### Named Routes Setup
```dart
MaterialApp(
  initialRoute: '/',
  routes: {
    '/': (context) => HomeScreen(),
    '/login': (context) => LoginScreen(),
    '/profile': (context) => ProfileScreen(),
    '/settings': (context) => SettingsScreen(),
  },
  // Dynamic routes with arguments
  onGenerateRoute: (settings) {
    if (settings.name == '/product') {
      final args = settings.arguments as ProductArgs;
      return MaterialPageRoute(
        builder: (context) => ProductScreen(product: args.product),
        settings: settings,
      );
    }
    return MaterialPageRoute(builder: (_) => NotFoundScreen());
  },
  // Fallback route
  onUnknownRoute: (settings) =>
      MaterialPageRoute(builder: (_) => NotFoundScreen()),
)
```

### GoRouter (recommended for Flutter 3.x)
```dart
// pubspec.yaml: go_router: ^13.0.0

import 'package:go_router/go_router.dart';

final router = GoRouter(
  initialLocation: '/',
  redirect: (context, state) {
    final isLoggedIn = AuthService.isLoggedIn;
    final isLoggingIn = state.matchedLocation == '/login';
    if (!isLoggedIn && !isLoggingIn) return '/login';
    if (isLoggedIn && isLoggingIn) return '/';
    return null;
  },
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => HomeScreen(),
    ),
    GoRoute(
      path: '/login',
      builder: (context, state) => LoginScreen(),
    ),
    GoRoute(
      path: '/product/:id',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        final extra = state.extra as Product?;
        return ProductScreen(id: id, product: extra);
      },
    ),
    ShellRoute(
      builder: (context, state, child) => MainShell(child: child),
      routes: [
        GoRoute(path: '/home', builder: (_, __) => HomeTab()),
        GoRoute(path: '/search', builder: (_, __) => SearchTab()),
        GoRoute(path: '/profile', builder: (_, __) => ProfileTab()),
      ],
    ),
  ],
);

// In MaterialApp
MaterialApp.router(routerConfig: router)

// Navigation calls
context.go('/home')                      // replace stack
context.push('/product/42')             // push onto stack
context.push('/product/42', extra: product)  // pass object
context.pop()                           // go back
context.goNamed('profile')             // named navigation
context.canPop()                        // check if can go back
```

### Navigation with Result
```dart
// Push and wait for result
Future<void> _selectColor() async {
  final color = await Navigator.push<Color>(
    context,
    MaterialPageRoute(builder: (_) => ColorPickerScreen()),
  );
  if (color != null) {
    setState(() => _selectedColor = color);
  }
}

// In ColorPickerScreen — return result
Navigator.pop(context, selectedColor);
```

---

## Form Handling

### Complete Form Pattern
```dart
class RegistrationForm extends StatefulWidget {
  @override
  State<RegistrationForm> createState() => _RegistrationFormState();
}

class _RegistrationFormState extends State<RegistrationForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _nameFocus = FocusNode();
  final _emailFocus = FocusNode();
  final _passwordFocus = FocusNode();

  bool _obscurePassword = true;
  bool _isSubmitting = false;
  String? _serverError;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _nameFocus.dispose();
    _emailFocus.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    // Hide keyboard
    FocusScope.of(context).unfocus();

    // Clear server error
    setState(() => _serverError = null);

    // Validate all fields
    if (!_formKey.currentState!.validate()) return;

    // Save all field values (calls onSaved on each field)
    _formKey.currentState!.save();

    setState(() => _isSubmitting = true);

    try {
      await AuthService.register(
        name: _nameController.text.trim(),
        email: _emailController.text.trim().toLowerCase(),
        password: _passwordController.text,
      );
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/home');
      }
    } on AuthException catch (e) {
      setState(() => _serverError = e.message);
    } catch (e) {
      setState(() => _serverError = 'Something went wrong. Please try again.');
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      autovalidateMode: AutovalidateMode.onUserInteraction,  // validate as user types
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Server-level error
          if (_serverError != null)
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red[50],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(_serverError!, style: TextStyle(color: Colors.red)),
            ),

          SizedBox(height: 16),

          // Name field
          TextFormField(
            controller: _nameController,
            focusNode: _nameFocus,
            keyboardType: TextInputType.name,
            textCapitalization: TextCapitalization.words,
            textInputAction: TextInputAction.next,
            decoration: InputDecoration(
              labelText: 'Full Name',
              prefixIcon: Icon(Icons.person_outline),
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Name is required';
              }
              if (value.trim().length < 2) {
                return 'Name must be at least 2 characters';
              }
              return null;
            },
            onFieldSubmitted: (_) =>
                FocusScope.of(context).requestFocus(_emailFocus),
          ),

          SizedBox(height: 16),

          // Email field
          TextFormField(
            controller: _emailController,
            focusNode: _emailFocus,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            decoration: InputDecoration(
              labelText: 'Email',
              prefixIcon: Icon(Icons.email_outlined),
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              if (value == null || value.trim().isEmpty) return 'Email is required';
              final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
              if (!emailRegex.hasMatch(value.trim())) return 'Enter a valid email';
              return null;
            },
            onFieldSubmitted: (_) =>
                FocusScope.of(context).requestFocus(_passwordFocus),
          ),

          SizedBox(height: 16),

          // Password field
          TextFormField(
            controller: _passwordController,
            focusNode: _passwordFocus,
            obscureText: _obscurePassword,
            textInputAction: TextInputAction.done,
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: Icon(Icons.lock_outline),
              suffixIcon: IconButton(
                icon: Icon(
                  _obscurePassword ? Icons.visibility_off : Icons.visibility,
                ),
                onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
              ),
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              if (value == null || value.isEmpty) return 'Password is required';
              if (value.length < 8) return 'Password must be at least 8 characters';
              if (!value.contains(RegExp(r'[A-Z]'))) return 'Include an uppercase letter';
              if (!value.contains(RegExp(r'[0-9]'))) return 'Include a number';
              return null;
            },
            onFieldSubmitted: (_) => _submit(),
          ),

          SizedBox(height: 24),

          // Submit button
          ElevatedButton(
            onPressed: _isSubmitting ? null : _submit,
            style: ElevatedButton.styleFrom(
              minimumSize: Size.fromHeight(48),
            ),
            child: _isSubmitting
                ? SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : Text('Create Account'),
          ),
        ],
      ),
    );
  }
}
```

### Form Validation Helpers
```dart
class Validators {
  static String? required(String? value, [String fieldName = 'This field']) {
    if (value == null || value.trim().isEmpty) return '$fieldName is required';
    return null;
  }

  static String? email(String? value) {
    if (value == null || value.trim().isEmpty) return 'Email is required';
    final regex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!regex.hasMatch(value.trim())) return 'Enter a valid email';
    return null;
  }

  static String? minLength(int min) => (String? value) {
    if (value == null || value.length < min) return 'Minimum $min characters';
    return null;
  };

  static String? phone(String? value) {
    if (value == null || value.isEmpty) return 'Phone is required';
    final regex = RegExp(r'^\+?[\d\s\-\(\)]{10,}$');
    if (!regex.hasMatch(value)) return 'Enter a valid phone number';
    return null;
  }

  // Combine validators
  static String? Function(String?) compose(List<String? Function(String?)> validators) {
    return (value) {
      for (final v in validators) {
        final error = v(value);
        if (error != null) return error;
      }
      return null;
    };
  }
}
```

---

## Async / Future Patterns

### Basic async/await
```dart
Future<void> fetchAndDisplay() async {
  setState(() => _isLoading = true);
  try {
    final data = await ApiService.getData();
    setState(() {
      _data = data;
      _error = null;
    });
  } on NetworkException catch (e) {
    setState(() => _error = 'Network error: ${e.message}');
  } on TimeoutException {
    setState(() => _error = 'Request timed out. Please try again.');
  } catch (e) {
    setState(() => _error = 'Unexpected error: $e');
  } finally {
    if (mounted) setState(() => _isLoading = false);
  }
}
```

### Parallel futures
```dart
Future<void> fetchAll() async {
  try {
    // Run both concurrently
    final results = await Future.wait([
      ApiService.getUser(userId),
      ApiService.getPosts(userId),
    ]);
    final user = results[0] as User;
    final posts = results[1] as List<Post>;
    setState(() {
      _user = user;
      _posts = posts;
    });
  } catch (e) {
    // One failure cancels all
    setState(() => _error = e.toString());
  }
}

// With timeout
final data = await ApiService.getData().timeout(
  Duration(seconds: 10),
  onTimeout: () => throw TimeoutException('Request timed out'),
);

// Sequence — second depends on first
Future<void> fetchSequential() async {
  final user = await ApiService.getUser(userId);
  final orders = await ApiService.getOrders(user.id);
  setState(() { _user = user; _orders = orders; });
}
```

### Compute (run in background isolate)
```dart
import 'package:flutter/foundation.dart';

Future<List<ProcessedItem>> processHeavyData(List<RawItem> raw) async {
  // Runs on a separate isolate — won't block UI
  return await compute(_processItems, raw);
}

// Must be top-level or static
List<ProcessedItem> _processItems(List<RawItem> raw) {
  return raw.map((item) => ProcessedItem.from(item)).toList();
}
```

---

## Stream Patterns

```dart
// Creating a stream controller
final _controller = StreamController<String>.broadcast();

// Add to stream
_controller.sink.add('Hello');
_controller.sink.addError(Exception('Error'));

// Close stream
await _controller.close();

// Stream with periodic data
final stream = Stream.periodic(Duration(seconds: 1), (count) => count);

// Transform streams
final doubled = stream.map((n) => n * 2);
final filtered = stream.where((n) => n.isEven);
final first5 = stream.take(5);

// Combining streams
final combined = StreamGroup.merge([stream1, stream2]);

// StreamController in StatefulWidget
class _MyWidgetState extends State<MyWidget> {
  late StreamSubscription<Data> _subscription;

  @override
  void initState() {
    super.initState();
    _subscription = DataService.stream.listen(
      (data) {
        if (mounted) setState(() => _data = data);
      },
      onError: (error) {
        if (mounted) setState(() => _error = error.toString());
      },
      onDone: () => print('Stream closed'),
    );
  }

  @override
  void dispose() {
    _subscription.cancel();  // IMPORTANT: always cancel
    super.dispose();
  }
}
```

---

## State Management with Provider

```dart
// pubspec.yaml: provider: ^6.1.2

// 1. Define ChangeNotifier
class CartProvider extends ChangeNotifier {
  List<CartItem> _items = [];

  List<CartItem> get items => List.unmodifiable(_items);
  int get itemCount => _items.length;
  double get total => _items.fold(0, (sum, item) => sum + item.total);

  void addItem(Product product) {
    final existing = _items.indexWhere((i) => i.productId == product.id);
    if (existing >= 0) {
      _items[existing] = _items[existing].copyWith(
        quantity: _items[existing].quantity + 1,
      );
    } else {
      _items.add(CartItem(productId: product.id, product: product));
    }
    notifyListeners();  // ← triggers rebuild of Consumers
  }

  void removeItem(String productId) {
    _items.removeWhere((i) => i.productId == productId);
    notifyListeners();
  }

  void clear() {
    _items.clear();
    notifyListeners();
  }
}

// 2. Provide at the top of the widget tree
void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => CartProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProxyProvider<AuthProvider, UserProvider>(
          create: (_) => UserProvider(),
          update: (_, auth, user) => user!..updateAuth(auth),
        ),
      ],
      child: MyApp(),
    ),
  );
}

// 3. Consume — full rebuild
class CartBadge extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final count = context.watch<CartProvider>().itemCount;
    return Badge(label: Text('$count'));
  }
}

// 4. Consume — selective (avoids unnecessary rebuilds)
class CartTotal extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final total = context.select<CartProvider, double>((cart) => cart.total);
    return Text('\$${total.toStringAsFixed(2)}');
  }
}

// 5. Read without listening (for callbacks — no rebuild)
ElevatedButton(
  onPressed: () => context.read<CartProvider>().addItem(product),
  child: Text('Add to Cart'),
)

// 6. Consumer widget (when you need a mix of rebuild and no-rebuild)
Consumer<CartProvider>(
  builder: (context, cart, child) {
    return Column(
      children: [
        child!,                        // static portion — not rebuilt
        Text('Items: ${cart.itemCount}'),
      ],
    );
  },
  child: Text('Cart'),               // not rebuilt on notifyListeners
)
```

---

## State Management with Riverpod

```dart
// pubspec.yaml: flutter_riverpod: ^2.5.1

import 'package:flutter_riverpod/flutter_riverpod.dart';

// 1. Providers (outside widget, top-level or in a separate file)

// Simple state
final counterProvider = StateProvider<int>((ref) => 0);

// Computed state (derived)
final doubleCountProvider = Provider<int>((ref) {
  return ref.watch(counterProvider) * 2;
});

// Async state
final userProvider = FutureProvider.family<User, String>((ref, userId) async {
  return ApiService.getUser(userId);
});

// Complex state with StateNotifier
class TodoNotifier extends StateNotifier<List<Todo>> {
  TodoNotifier() : super([]);

  void add(String title) {
    state = [...state, Todo(title: title)];
  }

  void toggle(String id) {
    state = state.map((todo) {
      return todo.id == id ? todo.copyWith(done: !todo.done) : todo;
    }).toList();
  }

  void remove(String id) {
    state = state.where((todo) => todo.id != id).toList();
  }
}

final todoProvider = StateNotifierProvider<TodoNotifier, List<Todo>>((ref) {
  return TodoNotifier();
});

// AsyncNotifier (Riverpod 2.x)
class PostsNotifier extends AsyncNotifier<List<Post>> {
  @override
  Future<List<Post>> build() async {
    return ApiService.getPosts();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => ApiService.getPosts());
  }
}

final postsProvider = AsyncNotifierProvider<PostsNotifier, List<Post>>(() {
  return PostsNotifier();
});

// 2. Setup
void main() {
  runApp(
    ProviderScope(
      child: MyApp(),
    ),
  );
}

// 3. Widget extends ConsumerWidget (replaces StatelessWidget)
class CounterWidget extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(counterProvider);
    return Column(
      children: [
        Text('Count: $count'),
        ElevatedButton(
          onPressed: () => ref.read(counterProvider.notifier).state++,
          child: Text('Increment'),
        ),
      ],
    );
  }
}

// 4. ConsumerStatefulWidget
class PostList extends ConsumerStatefulWidget {
  @override
  ConsumerState<PostList> createState() => _PostListState();
}

class _PostListState extends ConsumerState<PostList> {
  @override
  Widget build(BuildContext context) {
    final postsAsync = ref.watch(postsProvider);
    return postsAsync.when(
      data: (posts) => ListView.builder(
        itemCount: posts.length,
        itemBuilder: (_, i) => ListTile(title: Text(posts[i].title)),
      ),
      loading: () => CircularProgressIndicator(),
      error: (err, stack) => Text('Error: $err'),
    );
  }
}
```

---

## State Management with BLoC

```dart
// pubspec.yaml: flutter_bloc: ^8.1.5

import 'package:flutter_bloc/flutter_bloc.dart';

// Events
abstract class AuthEvent {}
class LoginRequested extends AuthEvent {
  final String email;
  final String password;
  LoginRequested({required this.email, required this.password});
}
class LogoutRequested extends AuthEvent {}

// States
abstract class AuthState {}
class AuthInitial extends AuthState {}
class AuthLoading extends AuthState {}
class AuthAuthenticated extends AuthState {
  final User user;
  AuthAuthenticated(this.user);
}
class AuthUnauthenticated extends AuthState {}
class AuthError extends AuthState {
  final String message;
  AuthError(this.message);
}

// BLoC
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _repository;

  AuthBloc(this._repository) : super(AuthInitial()) {
    on<LoginRequested>(_onLoginRequested);
    on<LogoutRequested>(_onLogoutRequested);
  }

  Future<void> _onLoginRequested(
    LoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      final user = await _repository.login(event.email, event.password);
      emit(AuthAuthenticated(user));
    } on AuthException catch (e) {
      emit(AuthError(e.message));
    }
  }

  Future<void> _onLogoutRequested(
    LogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    await _repository.logout();
    emit(AuthUnauthenticated());
  }
}

// Provide
BlocProvider(
  create: (context) => AuthBloc(context.read<AuthRepository>()),
  child: LoginScreen(),
)

// Consume
BlocBuilder<AuthBloc, AuthState>(
  builder: (context, state) {
    if (state is AuthLoading) return CircularProgressIndicator();
    if (state is AuthAuthenticated) return HomeScreen(user: state.user);
    if (state is AuthError) return ErrorText(state.message);
    return LoginForm();
  },
)

// Listen for side effects
BlocListener<AuthBloc, AuthState>(
  listener: (context, state) {
    if (state is AuthAuthenticated) {
      Navigator.pushReplacementNamed(context, '/home');
    }
    if (state is AuthError) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(state.message)));
    }
  },
  child: LoginForm(),
)

// Both Builder + Listener
BlocConsumer<AuthBloc, AuthState>(
  listener: (context, state) { /* side effects */ },
  builder: (context, state) { return Widget(); },
)

// Dispatch event
context.read<AuthBloc>().add(LoginRequested(email: email, password: password));
```

---

## Repository Pattern

```dart
// Abstract repository interface
abstract class UserRepository {
  Future<User> getUser(String id);
  Future<List<User>> getUsers();
  Future<User> createUser(CreateUserDto dto);
  Future<User> updateUser(String id, UpdateUserDto dto);
  Future<void> deleteUser(String id);
}

// Remote implementation
class RemoteUserRepository implements UserRepository {
  final ApiClient _client;

  RemoteUserRepository(this._client);

  @override
  Future<User> getUser(String id) async {
    final response = await _client.get('/users/$id');
    return User.fromJson(response.data);
  }

  @override
  Future<List<User>> getUsers() async {
    final response = await _client.get('/users');
    return (response.data as List).map((j) => User.fromJson(j)).toList();
  }
  // ...
}

// Cached implementation (wraps remote)
class CachedUserRepository implements UserRepository {
  final UserRepository _remote;
  final Map<String, User> _cache = {};

  CachedUserRepository(this._remote);

  @override
  Future<User> getUser(String id) async {
    if (_cache.containsKey(id)) return _cache[id]!;
    final user = await _remote.getUser(id);
    _cache[id] = user;
    return user;
  }
  // ...
}
```

---

## List & Grid Patterns

### Reorderable List
```dart
ReorderableListView.builder(
  itemCount: _items.length,
  itemBuilder: (context, index) => ListTile(
    key: ValueKey(_items[index].id),  // Key required
    title: Text(_items[index].title),
    trailing: ReorderableDragStartListener(
      index: index,
      child: Icon(Icons.drag_handle),
    ),
  ),
  onReorder: (oldIndex, newIndex) {
    setState(() {
      if (newIndex > oldIndex) newIndex--;
      final item = _items.removeAt(oldIndex);
      _items.insert(newIndex, item);
    });
  },
)
```

### Sliver List for complex scrolling
```dart
CustomScrollView(
  slivers: [
    SliverAppBar(
      title: Text('My App'),
      floating: true,
      snap: true,
      expandedHeight: 200,
      flexibleSpace: FlexibleSpaceBar(
        background: Image.asset('header.jpg', fit: BoxFit.cover),
      ),
    ),
    SliverToBoxAdapter(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Text('Featured', style: TextStyle(fontSize: 20)),
      ),
    ),
    SliverGrid(
      delegate: SliverChildBuilderDelegate(
        (context, index) => Card(child: Center(child: Text('$index'))),
        childCount: 6,
      ),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2, crossAxisSpacing: 8, mainAxisSpacing: 8,
      ),
    ),
    SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) => ListTile(title: Text('Item $index')),
        childCount: 20,
      ),
    ),
  ],
)
```

---

## Search & Filter Pattern

```dart
class SearchScreen extends StatefulWidget {
  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _searchController = TextEditingController();
  List<Item> _allItems = [];
  List<Item> _filtered = [];
  String _query = '';

  @override
  void initState() {
    super.initState();
    _allItems = getAllItems();
    _filtered = _allItems;
    _searchController.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged() {
    final query = _searchController.text.toLowerCase().trim();
    if (query == _query) return;
    setState(() {
      _query = query;
      _filtered = query.isEmpty
          ? _allItems
          : _allItems.where((item) {
              return item.name.toLowerCase().contains(query) ||
                  item.description.toLowerCase().contains(query);
            }).toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: EdgeInsets.all(16),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: 'Search...',
              prefixIcon: Icon(Icons.search),
              suffixIcon: _query.isNotEmpty
                  ? IconButton(
                      icon: Icon(Icons.clear),
                      onPressed: () {
                        _searchController.clear();
                        FocusScope.of(context).unfocus();
                      },
                    )
                  : null,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
        Expanded(
          child: _filtered.isEmpty
              ? Center(child: Text('No results for "$_query"'))
              : ListView.builder(
                  itemCount: _filtered.length,
                  itemBuilder: (_, i) => ListTile(title: Text(_filtered[i].name)),
                ),
        ),
      ],
    );
  }
}
```

---

## Pagination Pattern

```dart
class PaginatedListScreen extends StatefulWidget {
  @override
  State<PaginatedListScreen> createState() => _PaginatedListScreenState();
}

class _PaginatedListScreenState extends State<PaginatedListScreen> {
  final ScrollController _scrollController = ScrollController();
  List<Post> _posts = [];
  int _page = 1;
  bool _isLoading = false;
  bool _hasMore = true;
  static const int _limit = 20;

  @override
  void initState() {
    super.initState();
    _fetchPage();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    final pos = _scrollController.position;
    // Trigger load when 200px from bottom
    if (pos.pixels >= pos.maxScrollExtent - 200) {
      if (!_isLoading && _hasMore) _fetchPage();
    }
  }

  Future<void> _fetchPage() async {
    if (_isLoading) return;
    setState(() => _isLoading = true);
    try {
      final newPosts = await ApiService.getPosts(page: _page, limit: _limit);
      setState(() {
        _posts.addAll(newPosts);
        _page++;
        _hasMore = newPosts.length == _limit;
      });
    } catch (e) {
      // show error
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _refresh() async {
    setState(() {
      _posts.clear();
      _page = 1;
      _hasMore = true;
    });
    await _fetchPage();
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView.builder(
        controller: _scrollController,
        itemCount: _posts.length + (_hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _posts.length) {
            return Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator()),
            );
          }
          return PostCard(post: _posts[index]);
        },
      ),
    );
  }
}
```

---

## Pull to Refresh

```dart
RefreshIndicator(
  onRefresh: () async {
    await _fetchData();
  },
  color: Colors.blue,
  backgroundColor: Colors.white,
  strokeWidth: 2,
  child: ListView.builder(
    physics: AlwaysScrollableScrollPhysics(),  // enable drag even when short
    itemCount: _items.length,
    itemBuilder: (_, i) => ListTile(title: Text(_items[i].title)),
  ),
)
```

---

## Local Storage with SharedPreferences

```dart
// pubspec.yaml: shared_preferences: ^2.2.3

import 'package:shared_preferences/shared_preferences.dart';

class PrefsService {
  static late SharedPreferences _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // String
  static String? getString(String key) => _prefs.getString(key);
  static Future<bool> setString(String key, String value) => _prefs.setString(key, value);

  // Bool
  static bool getBool(String key, {bool defaultValue = false}) =>
      _prefs.getBool(key) ?? defaultValue;
  static Future<bool> setBool(String key, bool value) => _prefs.setBool(key, value);

  // Int
  static int getInt(String key, {int defaultValue = 0}) =>
      _prefs.getInt(key) ?? defaultValue;
  static Future<bool> setInt(String key, int value) => _prefs.setInt(key, value);

  // Object as JSON
  static T? getObject<T>(String key, T Function(Map<String, dynamic>) fromJson) {
    final jsonStr = _prefs.getString(key);
    if (jsonStr == null) return null;
    return fromJson(jsonDecode(jsonStr) as Map<String, dynamic>);
  }
  static Future<bool> setObject(String key, Object value) =>
      _prefs.setString(key, jsonEncode(value));

  // Remove / clear
  static Future<bool> remove(String key) => _prefs.remove(key);
  static Future<bool> clear() => _prefs.clear();
}

// Usage
await PrefsService.init();  // in main()
await PrefsService.setString('token', token);
final token = PrefsService.getString('token');
await PrefsService.setBool('onboarded', true);
```

---

## HTTP & API Calls

### Using http package
```dart
// pubspec.yaml: http: ^1.2.1

import 'package:http/http.dart' as http;

class ApiClient {
  final String baseUrl;
  final Map<String, String> _defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  ApiClient({required this.baseUrl});

  Map<String, String> _headers([String? token]) => {
    ..._defaultHeaders,
    if (token != null) 'Authorization': 'Bearer $token',
  };

  Future<T> get<T>(String path, T Function(dynamic) fromJson, {String? token}) async {
    final response = await http.get(
      Uri.parse('$baseUrl$path'),
      headers: _headers(token),
    ).timeout(Duration(seconds: 15));
    return _handleResponse(response, fromJson);
  }

  Future<T> post<T>(String path, Object body, T Function(dynamic) fromJson, {String? token}) async {
    final response = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: _headers(token),
      body: jsonEncode(body),
    ).timeout(Duration(seconds: 15));
    return _handleResponse(response, fromJson);
  }

  T _handleResponse<T>(http.Response response, T Function(dynamic) fromJson) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return fromJson(jsonDecode(response.body));
    } else if (response.statusCode == 401) {
      throw UnauthorizedException();
    } else if (response.statusCode == 404) {
      throw NotFoundException(response.body);
    } else {
      throw ApiException(response.statusCode, response.body);
    }
  }
}
```

### Using Dio (popular alternative)
```dart
// pubspec.yaml: dio: ^5.4.3

import 'package:dio/dio.dart';

final dio = Dio(BaseOptions(
  baseUrl: 'https://api.example.com',
  connectTimeout: Duration(seconds: 10),
  receiveTimeout: Duration(seconds: 15),
  headers: {'Accept': 'application/json'},
));

// Interceptor for auth token
dio.interceptors.add(InterceptorsWrapper(
  onRequest: (options, handler) async {
    final token = await SecureStorage.getToken();
    if (token != null) options.headers['Authorization'] = 'Bearer $token';
    handler.next(options);
  },
  onError: (error, handler) async {
    if (error.response?.statusCode == 401) {
      // try token refresh...
    }
    handler.next(error);
  },
));

// GET
final response = await dio.get<Map<String, dynamic>>('/users/$id');
final user = User.fromJson(response.data!);

// POST
await dio.post('/users', data: {'name': name, 'email': email});

// Upload file
await dio.post(
  '/upload',
  data: FormData.fromMap({
    'file': await MultipartFile.fromFile(file.path, filename: 'photo.jpg'),
  }),
  onSendProgress: (sent, total) => print('${sent / total * 100}%'),
);
```

---

## JSON Serialization

### Manual
```dart
class User {
  final String id;
  final String name;
  final String email;
  final DateTime createdAt;
  final Address? address;

  const User({
    required this.id,
    required this.name,
    required this.email,
    required this.createdAt,
    this.address,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'] as String,
    name: json['name'] as String,
    email: json['email'] as String,
    createdAt: DateTime.parse(json['created_at'] as String),
    address: json['address'] != null
        ? Address.fromJson(json['address'] as Map<String, dynamic>)
        : null,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'email': email,
    'created_at': createdAt.toIso8601String(),
    if (address != null) 'address': address!.toJson(),
  };

  User copyWith({String? id, String? name, String? email, Address? address}) => User(
    id: id ?? this.id,
    name: name ?? this.name,
    email: email ?? this.email,
    createdAt: createdAt,
    address: address ?? this.address,
  );

  @override
  String toString() => 'User(id: $id, name: $name, email: $email)';

  @override
  bool operator ==(Object other) =>
      identical(this, other) || (other is User && other.id == id);

  @override
  int get hashCode => id.hashCode;
}
```

### With json_serializable (code gen)
```dart
// pubspec.yaml:
// dependencies: json_annotation: ^4.9.0
// dev_dependencies: json_serializable: ^6.7.1, build_runner: ^2.4.8

import 'package:json_annotation/json_annotation.dart';

part 'user.g.dart';  // generated file

@JsonSerializable(explicitToJson: true)
class User {
  final String id;
  final String name;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  User({required this.id, required this.name, required this.createdAt});

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
  Map<String, dynamic> toJson() => _$UserToJson(this);
}

// Generate: flutter pub run build_runner build
```

---

## Error Handling Patterns

```dart
// Custom exceptions
class AppException implements Exception {
  final String message;
  final int? statusCode;
  const AppException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class NetworkException extends AppException {
  const NetworkException([String message = 'No internet connection'])
      : super(message, statusCode: null);
}

class ServerException extends AppException {
  const ServerException(String message, int statusCode)
      : super(message, statusCode: statusCode);
}

class ValidationException extends AppException {
  final Map<String, String> fieldErrors;
  const ValidationException(this.fieldErrors) : super('Validation failed');
}

// Result type pattern (avoids exceptions for expected errors)
sealed class Result<T> {
  const Result();
}

class Success<T> extends Result<T> {
  final T data;
  const Success(this.data);
}

class Failure<T> extends Result<T> {
  final String message;
  final Object? error;
  const Failure(this.message, {this.error});
}

// Usage
Future<Result<User>> fetchUser(String id) async {
  try {
    final user = await _repository.getUser(id);
    return Success(user);
  } on NetworkException catch (e) {
    return Failure('Please check your internet connection', error: e);
  } on ServerException catch (e) {
    return Failure(e.message, error: e);
  }
}

// In widget
final result = await fetchUser(userId);
switch (result) {
  case Success(data: final user):
    setState(() => _user = user);
  case Failure(message: final msg):
    setState(() => _error = msg);
}
```

---

## Responsive Layout Pattern

```dart
// Breakpoints
class Breakpoints {
  static const mobile = 600;
  static const tablet = 1024;

  static bool isMobile(BuildContext context) =>
      MediaQuery.of(context).size.width < mobile;
  static bool isTablet(BuildContext context) {
    final w = MediaQuery.of(context).size.width;
    return w >= mobile && w < tablet;
  }
  static bool isDesktop(BuildContext context) =>
      MediaQuery.of(context).size.width >= tablet;
}

// Responsive builder
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget? desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    this.desktop,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 1024 && desktop != null) return desktop!;
        if (constraints.maxWidth >= 600 && tablet != null) return tablet!;
        return mobile;
      },
    );
  }
}

// Usage
ResponsiveLayout(
  mobile: MobileProductCard(product: product),
  tablet: TabletProductCard(product: product),
  desktop: DesktopProductCard(product: product),
)
```

---

## Theme Switching Pattern

```dart
// Using Provider
class ThemeProvider extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.system;

  ThemeMode get themeMode => _themeMode;
  bool get isDark => _themeMode == ThemeMode.dark;

  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    notifyListeners();
    await PrefsService.setString('theme', mode.name);
  }

  Future<void> loadTheme() async {
    final saved = PrefsService.getString('theme');
    if (saved != null) {
      _themeMode = ThemeMode.values.byName(saved);
      notifyListeners();
    }
  }

  void toggle() => setThemeMode(isDark ? ThemeMode.light : ThemeMode.dark);
}

// In MaterialApp
MaterialApp(
  themeMode: context.watch<ThemeProvider>().themeMode,
  theme: AppTheme.light,
  darkTheme: AppTheme.dark,
)
```

---

## Debouncing & Throttling

```dart
// Debounce — delays execution, resets timer on each call
class Debouncer {
  final Duration delay;
  Timer? _timer;

  Debouncer({required this.delay});

  void call(VoidCallback action) {
    _timer?.cancel();
    _timer = Timer(delay, action);
  }

  void dispose() => _timer?.cancel();
}

// Usage in search
final _debouncer = Debouncer(delay: Duration(milliseconds: 400));

void _onSearchChanged(String query) {
  _debouncer(() => _performSearch(query));
}

// Throttle — allows max one call per duration
class Throttler {
  final Duration interval;
  DateTime? _lastCall;

  Throttler({required this.interval});

  void call(VoidCallback action) {
    final now = DateTime.now();
    if (_lastCall == null || now.difference(_lastCall!) >= interval) {
      _lastCall = now;
      action();
    }
  }
}
```

---

## Keys in Flutter

```dart
// ValueKey — based on value equality
ListView.builder(
  itemBuilder: (_, i) => ListTile(
    key: ValueKey(items[i].id),   // stable identity for diffing
    title: Text(items[i].title),
  ),
)

// GlobalKey — access state from outside the widget tree
final _formKey = GlobalKey<FormState>();
final _scaffoldKey = GlobalKey<ScaffoldState>();

_formKey.currentState!.validate()
_formKey.currentState!.save()
_scaffoldKey.currentState!.openDrawer()

// UniqueKey — forces widget to rebuild (e.g., reset state)
Image(key: UniqueKey(), image: NetworkImage(url))  // reload image

// PageStorageKey — preserves scroll position when switching tabs
ListView(key: PageStorageKey('tab-1'), ...)

// ObjectKey — identity based on object reference
ListTile(key: ObjectKey(user))
```

---

## Extension Methods

```dart
// String extensions
extension StringX on String {
  String get capitalizeFirst =>
      isEmpty ? this : '${this[0].toUpperCase()}${substring(1)}';

  String get camelToWords => replaceAllMapped(
    RegExp(r'[A-Z]'),
    (match) => ' ${match.group(0)!.toLowerCase()}',
  ).trim();

  bool get isValidEmail =>
      RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(this);

  String truncate(int maxLength, {String ellipsis = '...'}) =>
      length > maxLength ? '${substring(0, maxLength)}$ellipsis' : this;
}

// DateTime extensions
extension DateTimeX on DateTime {
  String get formatted => '${day.toString().padLeft(2, '0')}/'
      '${month.toString().padLeft(2, '0')}/$year';

  bool get isToday {
    final now = DateTime.now();
    return year == now.year && month == now.month && day == now.day;
  }

  String get timeAgo {
    final diff = DateTime.now().difference(this);
    if (diff.inMinutes < 1) return 'just now';
    if (diff.inHours < 1) return '${diff.inMinutes}m ago';
    if (diff.inDays < 1) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return formatted;
  }
}

// BuildContext extensions
extension ContextX on BuildContext {
  ThemeData get theme => Theme.of(this);
  ColorScheme get colors => Theme.of(this).colorScheme;
  TextTheme get textTheme => Theme.of(this).textTheme;
  MediaQueryData get mediaQuery => MediaQuery.of(this);
  double get screenWidth => mediaQuery.size.width;
  double get screenHeight => mediaQuery.size.height;
  bool get isDark => theme.brightness == Brightness.dark;

  void showSnack(String message) {
    ScaffoldMessenger.of(this).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}

// num extensions
extension NumX on num {
  Widget get verticalSpace => SizedBox(height: toDouble());
  Widget get horizontalSpace => SizedBox(width: toDouble());
  EdgeInsets get allPadding => EdgeInsets.all(toDouble());
}

// Usage: 16.verticalSpace, 8.horizontalSpace, 'hello'.capitalizeFirst
```

---

## Named Constructors & Factory

```dart
class ApiResponse<T> {
  final T? data;
  final String? error;
  final bool isLoading;

  const ApiResponse._({this.data, this.error, this.isLoading = false});

  factory ApiResponse.loading() => ApiResponse._(isLoading: true);
  factory ApiResponse.success(T data) => ApiResponse._(data: data);
  factory ApiResponse.error(String message) => ApiResponse._(error: message);

  bool get hasData => data != null;
  bool get hasError => error != null;

  R when<R>({
    required R Function() loading,
    required R Function(T data) success,
    required R Function(String error) error,
  }) {
    if (isLoading) return loading();
    if (hasError) return this.error!(this.error!);
    return success(data as T);
  }
}

// Usage
final state = ApiResponse<User>.loading();
final success = ApiResponse.success(user);
final failure = ApiResponse<User>.error('Not found');

state.when(
  loading: () => CircularProgressIndicator(),
  success: (user) => UserCard(user: user),
  error: (msg) => Text('Error: $msg'),
)
```

---

*Last updated: Flutter 3.x / Dart 3.x*
