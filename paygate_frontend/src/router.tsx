import { createBrowserRouter } from 'react-router-dom'
import AppLayout from './ui/AppLayout'
import LoginPage from './routes/LoginPage'
import RegisterPage from './routes/RegisterPage'
import DashboardPage from './routes/dashboard/DashboardPage'
import RefundPage from  './routes/Refundpage/RefundPage'
import OrderPage from './routes/Orderpage/OrderPage'
import AdminOnboardingPage from './routes/AdminOnboardingPage/AdminOnboardingPage'  
import Protected from './routes/Protected'



export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Protected><DashboardPage /></Protected> },
      {path: 'orders',element:<Protected><OrderPage/></Protected>},
      {path:'refund',element:<Protected><RefundPage/></Protected>},
      {path:'admin-onboard',element:<Protected><AdminOnboardingPage/></Protected>},
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
    ]
  }
])


