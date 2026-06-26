import 'package:flutter/material.dart';

void main() {
  runApp(const KeyCadenceDemo());
}

class KeyCadenceDemo extends StatelessWidget {
  const KeyCadenceDemo({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'KeyCadence Demo',
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
      ),
      home: const LoginScreen(),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final List<double> _keystrokeTimings = [];
  DateTime? _lastKeyPress;

  void _onKeyPress() {
    final now = DateTime.now();
    if (_lastKeyPress != null) {
      final gap = now.difference(_lastKeyPress!).inMilliseconds.toDouble();
      _keystrokeTimings.add(gap);
    }
    _lastKeyPress = now;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Banking Login')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.lock, size: 64, color: Colors.indigo),
            const SizedBox(height: 32),
            TextField(
              controller: _usernameController,
              decoration: const InputDecoration(
                labelText: 'Username',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _passwordController,
              obscureText: true,
              onChanged: (_) => _onKeyPress(),
              decoration: const InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        'Login attempted with ${_keystrokeTimings.length} keystroke timings',
                      ),
                    ),
                  );
                },
                child: const Text('Login'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
