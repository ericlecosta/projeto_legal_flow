import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

/** Registra falhas de chamadas à API em um único ponto e repassa o erro para quem chamou. */
export const httpErrorInterceptor: HttpInterceptorFn = (req, next) =>
  next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      console.error(`[API] ${req.method} ${req.urlWithParams} falhou (${error.status})`, error.message);
      return throwError(() => error);
    }),
  );
