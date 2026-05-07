import { RouterProvider } from 'react-router-dom';
import { Providers } from './providers';
import { router } from './router';
import { AuthGate } from './AuthGate';

export function App() {
  return (
    <Providers>
      <AuthGate>
        <RouterProvider router={router} />
      </AuthGate>
    </Providers>
  );
}

export default App;
