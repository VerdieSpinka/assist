import { authenticatedFetch } from './auth'

export interface BalanceResponse {
  balance: string
}

export async function getBalance(): Promise<BalanceResponse> {
  // Hanya teruskan endpoint relatif. `authenticatedFetch` akan menangani BASE_API_URL.
  const response = await authenticatedFetch('/api/billing/getBalance')

  // Penanganan error sudah dilakukan di dalam authenticatedFetch,
  // jadi pengecekan `!response.ok` di sini tidak lagi diperlukan.
  return response.json()
}