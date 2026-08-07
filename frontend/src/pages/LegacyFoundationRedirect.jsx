import { Navigate, useLocation, useParams } from 'react-router-dom';
import { getLegacyFoundationTarget } from '../utils/courseRoutes';

export default function LegacyFoundationRedirect() {
    const { moduleKey } = useParams();
    const location = useLocation();

    return (
        <Navigate
            replace
            to={getLegacyFoundationTarget(moduleKey)}
            state={location.state}
        />
    );
}
