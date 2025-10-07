import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../utils/auth'

export default function AppLayout() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isMerchant = user?.role === 'merchant'
  return (
    <div className="min-h-full">
      <nav className="border-b bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <Link to="/" className="text-lg font-semibold text-brand-700">PayGate</Link>
            <div className="flex items-center gap-4">
              {user ? (
                <>
                  <NavLink 
                    to="/" 
                    className={({isActive}) => 
                      `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive 
                          ? 'bg-emerald-100 text-emerald-700' 
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`
                    }
                  >
                    Dashboard
                  </NavLink>
                 { isMerchant  ? ( <> <NavLink 
                    to="/orders" 
                    className={({isActive}) => 
                      `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive 
                          ? 'bg-emerald-100 text-emerald-700' 
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`
                    }
                  >
                    Demo
                  </NavLink>
                   <NavLink 
                    to="/refund" 
                    className={({isActive}) => 
                      `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive 
                          ? 'bg-emerald-100 text-emerald-700' 
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`
                    }
                  >
                    Refund
                  </NavLink>
                  <button 
                    onClick={logout} 
                    className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
                  >
                    Logout
                  </button> 
                     </>):
                  ( 
                    <>
                    <NavLink 
                    to="/admin-onboard" 
                    className={({isActive}) => 
                      `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive 
                          ? 'bg-emerald-100 text-emerald-700' 
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`
                    }
                  >
                    Admin-OnBoard
                  </NavLink>
                  <button 
                    onClick={logout} 
                    className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
                  >
                    Logout
                  </button>
                  </>)}
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <NavLink 
                    to="/login" 
                    className={({isActive}) => 
                      `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive 
                          ? 'bg-emerald-100 text-emerald-700' 
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`
                    }
                  >
                    Login
                  </NavLink>
                  <NavLink 
                    to="/register" 
                    className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
                  >
                    Register
                  </NavLink>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl p-6">
        <Outlet />
      </main>
    </div>
  )
}


